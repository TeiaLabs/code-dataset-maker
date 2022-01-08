"""
Read repo_list_path, filter git URLs, and save a clone script to script_path.

Read repo lists in the format created by
python -m github_dataset_maker.get_repos --mode ranged as well.
"""
from __future__ import annotations

import itertools
from pathlib import Path
from typing import Iterable, List, Literal, Optional

from tap import Tap as TypedArgumentParser

from . import utils


def clone_each(
    repos_urls: Iterable[str],
    destination: Path,
    supported_files: Iterable[str],
    custom_ssh_key: Path | None = None,
) -> list[str]:

    base_command = "git clone --depth 1 {url} {folder}"
    if custom_ssh_key is not None and custom_ssh_key.is_file():
        base_command += f" --config core.sshCommand=ssh -i {custom_ssh_key}"
    or_regex = r"\|".join(supported_files)
    all_files_ending_in = rf".*.\({or_regex}\)"
    lines = []
    for url in repos_urls:
        org, repo = url.split("/")[-2:]
        if org.startswith("git@github.com:"):
            org = org[15:]
        if repo.endswith(".git"):
            repo = repo[:-4]
        output_path = destination / f"{org}/{repo}"
        cmd = base_command.format(url=url, folder=output_path)
        cmd += f" ; rm -rf {output_path / '.git'}"
        cmd += f" ; find {output_path} -type f ! -regex '{all_files_ending_in}' -delete"
        lines.append(cmd)
    return lines


class SupportedExtensions:
    mapping: dict[str, list[str]] = {
        "python": ["py"],
        "javascript": ["es", "es6", "js", "jsx", "ts", "tsx"],
        "java": [".java", ".class", ".apex", ".cls", ".kt", ".kts", ".ktm",".scala", ".sc"],
    }
    @classmethod
    def get(cls, *languages: str) -> Iterable[str]:
        return itertools.chain(*[cls.mapping[lang] for lang in languages])


def create_clone_script(repo_list_path: Path, destination_dir: Path, script_path: Path, languages: list[str]):
    txt_lines = utils.read_multiline_txt_file(repo_list_path)
    # TODO add support for org/repo paths
    repos_urls = filter(lambda x: x.startswith(("git", "https")), txt_lines)
    commands = clone_each(
        repos_urls,
        destination_dir,
        supported_files=SupportedExtensions.get(*languages),
    )
    utils.save_multiline_txt(script_path, commands, append=True)
    print("Done:", script_path)


class CloneScriptCreatorArgs(TypedArgumentParser):
    custom_ssh_key: Optional[Path] = None  # Path to the ssh key to use for cloning.
    destination_dir: Path = Path(".")  # Where to save the cloned repos
    languages: List[Literal["python", "javascript", "java"]]
    repo_list_path: Path  # Path to file containing repo URLs (one per line)
    script_path: Path = Path("clone.sh") # Path to save the created script
    split_lists: bool = False  # If true, glob repo_list_path for repo lists *.txt.
    split_scripts: bool = False  # If true, each repo_list will be saved to a separate script.

    def process_args(self) -> None:
        if self.split_scripts and not self.split_lists:
            raise ValueError("--split-scripts requires --split-lists.")


def main():
    args = CloneScriptCreatorArgs(underscores_to_dashes=True).parse_args()
    repo_lists = [args.repo_list_path]
    if args.split_lists:
        repo_lists = sorted(
            args.repo_list_path.glob(r"*.txt"),
            key=lambda x: int(x.stem.split("_")[-1].split("-")[0]),
        )
    for i, sub_list in enumerate(repo_lists):
        sub_script_path = args.script_path
        if args.split_scripts:
            sub_script_path = args.script_path.parent / f"{args.script_path.stem}_{i}.sh"
        create_clone_script(
            sub_list, args.destination_dir, sub_script_path, args.languages
        )


if __name__ == "__main__":
    main()
