"""
Read repo_list_path, filter git URLs, and save a clone script to script_path.

Read repo lists in the format created by
python -m github_dataset_maker.get_repos --mode ranged as well.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable


def read_multiline_txt_file(file_path: Path | str) -> list[str]:
    """Read a multiline text file and returns a list of lines."""
    with open(file_path, "r") as f:
        lines = f.read().split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def write_multiline_txt_file(file_path: Path | str, lines: list[str]):
    """Write a multiline text file."""
    with open(file_path, "a") as f:
        f.write("\n".join(lines))


def clone_each(
    repos_urls: Iterable[str],
    destination: Path,
    supported_files: Iterable[str] = ["es", "es6", "js", "jsx", "ts", "tsx", "py"],
    custom_ssh_key: Path | None = None,
) -> list[str]:

    base_command = "git clone --depth 1 {url} {folder}"
    if custom_ssh_key is not None and custom_ssh_key.is_file():
        base_command += f" --config core.sshCommand=ssh -i {custom_ssh_key}"
    or_regex = r"\|".join(supported_files)
    all_files_ending_in = rf".*\.\({or_regex}\)"
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


def create_clone_script(repo_list_path: Path, destination_dir: Path, script_path: Path):
    txt_lines = read_multiline_txt_file(repo_list_path)
    repos_urls = filter(lambda x: x.startswith("git"), txt_lines)
    commands = clone_each(
        repos_urls, destination_dir, custom_ssh_key=Path("~/.ssh/id_rsa-osf_github")
    )
    write_multiline_txt_file(script_path, commands)
    print("Done:", script_path)


if __name__ == "__main__":
    split_lists: bool = False
    # destination_dir = Path("/media/gaius/4tb-wd-blue/teia-python-repos")
    destination_dir = Path("/media/gaius/4tb-wd-blue/osf-javascript-repos")
    # input_path = Path("repo-lists/")
    input_path = Path("osf-repos.txt")
    script_path = Path("clone-all.sh")
    if split_lists:
        repo_lists = sorted(
            input_path.glob(r"*.txt"),
            key=lambda x: int(x.stem.split("_")[-1].split("-")[0]),
        )
        for repo_list_path in repo_lists:
            create_clone_script(repo_list_path, destination_dir, script_path)
    else:
        create_clone_script(input_path, destination_dir, script_path)
