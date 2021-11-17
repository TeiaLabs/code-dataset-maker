from __future__ import annotations

from pathlib import Path

COMAND = "git clone --depth 1 {url} {folder}"


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


def clone_each(repos_urls: list[str], destination: Path) -> list[str]:
    lines = []
    for url in repos_urls:
        org, repo = url.split("/")[-2:]
        output_path = destination / f"{org}/{repo}"
        cmd = COMAND.format(url=url, folder=output_path)
        cmd += f" ; rm -rf {output_path / '.git'}"
        cmd += f" ; find {output_path} -type f ! -name '*.py' -delete"
        lines.append(cmd)
    return lines


if __name__ == "__main__":
    repo_lists = sorted(Path("repo-lists").glob(r"*.txt"), key=lambda x: int(x.stem.split("_")[-1].split("-")[0]))
    for repo_list_path in repo_lists:
        repos_urls = read_multiline_txt_file(repo_list_path)
        destination = Path("/media/gaius/4tb-wd-blue/teia-python-repos")
        commands = clone_each(repos_urls, destination)
        write_multiline_txt_file(Path("clone-repos.sh"), commands)
        print("Done:", repo_list_path)
