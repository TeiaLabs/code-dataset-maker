from pathlib import Path

import github_repo_zip_downloader


def main():
    github_repo_zip_downloader.run("./repos-desc.txt", None, Path("new-dataset"))

main()
