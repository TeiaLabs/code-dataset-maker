from __future__ import annotations

import json
from multiprocessing.sharedctypes import Value
import os
import time
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Tuple, TypedDict

import pandas as pd
from dotenv import load_dotenv
from github import Github
from github.Repository import Repository
from tap import Tap as TypedArgumentParser

from .rate_limit import check_rate_limit, wait_on_rate_limits
from .supported_languages import programming_languages

load_dotenv()
API_TOKEN = os.environ["GITHUB_API_TOKEN"]


def export_to_csv(list_of_objs: Iterable[Mapping[str, Any]], csv_path: Path):
    """
    Create .csv file out of list of objs. Append to .csv if existing.

    Do not check if the headers match (to avoid wasting I/O).
    """
    df = pd.DataFrame.from_dict(list_of_objs)
    if csv_path.is_file():
        df.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        df.to_csv(csv_path, index=False)


class ArgParser(TypedArgumentParser):
    stars: Tuple[int, int]  # range of stars of repositories to be included in the dataset
    lang: str  # programming language
    output: str = None # filename to be used on the .json and .txt files
    step: int  # size of step in range of stars
    mode: Literal["exact", "greater-than", "ranged"]  # Search operator for the stars parameter of the query

    def check_args(self):
        super().configure()
        if self.lang not in programming_languages:
            msg = f"{self.lang} is not a supported programming language"
            raise ValueError(msg)
        if self.output is None:
            self.output = f"{self.lang}_{self.stars[0]}-{self.stars[1]}"


def save_json(repos: list, filename: Path | str) -> None:
    with open(filename, "w") as f:
        json.dump(repos, f, indent=2)


def save_multiline_txt(strings: list, filename: Path | str, append: bool = True) -> None:
    op = "a" if append else "w"
    with open(filename, op) as f:
        f.writelines(f"{s}\n" for s in strings)


class RepoInfo(TypedDict):
    url: str
    stars: int


def get_repo_info(repo: Repository) -> RepoInfo:
    print(f"{repo.name:<35}", f"{repo.stargazers_count:>15}", end="\r", flush=True)
    return {"url": repo.html_url, "stars": repo.stargazers_count}


@wait_on_rate_limits
def grab_repos_by_stars(stars: int, lang: str, bigger_than: bool = False) -> Iterable[Repository]:
    print(f"Getting repos with {stars} stars.")
    pygithub = Github(API_TOKEN)
    query = f"stars:{stars} language:{lang}"
    if bigger_than:
        query = f"stars:>{stars} language:{lang}"
    results = pygithub.search_repositories(
        query=query,
        sort="stars",
        order="desc",
    )
    return results


@wait_on_rate_limits
def grab_repos_by_stars_range(stars: tuple[int, int], lang: str) -> Iterable[Repository]:
    print(f"Getting repos within {stars} stars.")
    pygithub = Github(API_TOKEN)
    query = f"stars:{stars[0]}..{stars[1]} language:{lang}"
    results = pygithub.search_repositories(
        query=query,
        sort="stars",
        order="desc",
    )
    return results


def save(repos: list[RepoInfo], filename: str):
    """Save objects on a CSV file and save URLs on a TXT file."""
    print(f"Saving {len(repos)} repos to '{filename}'.")
    export_to_csv(repos, Path(f"{filename}.csv"))
    save_multiline_txt([repo["url"] for repo in repos], f"{filename}.txt")


def assemble_repo_info_and_save(repos: Iterable[Repository], filename: str):
    repo_info = []
    for i, repo in enumerate(repos):
        repo_info.append(get_repo_info(repo))
        if i % 30 == 0:
            check_rate_limit()
            # time.sleep(1)
    save(repo_info, filename)


def extract_and_save(
    stars: tuple[int, int],
    language: str,
    filename: str,
    step: int,
    mode: Literal["exact", "greater-than", "ranged"],
):
    # repos with exact number of stars
    if step == 0 and mode == "exact":
        results = grab_repos_by_stars(stars[0], language)
        assemble_repo_info_and_save(results, filename)
    # iterate over range of stars, repos with exact number of stars
    elif step == 1 and mode == "exact":
        for star_num in range(stars[0], stars[1]):
            results = grab_repos_by_stars(star_num, language)
            assemble_repo_info_and_save(results, f"{language}_{star_num}")
    # iterate over range of stars, repos within a range of stars
    elif step > 1 and mode == "ranged":
        for star_num in range(stars[0], stars[1], step):
            results = grab_repos_by_stars_range((star_num, star_num + step), language)
            assemble_repo_info_and_save(results, f"{language}_{star_num}-{star_num + step}")
    # bigger than a number of stars "step == 0 mode=greater-than"
    elif step == 0 and mode == "greater-than":
        results = grab_repos_by_stars(stars[0], language, bigger_than=True)
        assemble_repo_info_and_save(results, filename)
    # repos within a range of stars "step == 0 mode=ranged"
    elif step == 0 and mode == "ranged":
        results = grab_repos_by_stars_range(stars, language)
        assemble_repo_info_and_save(results, f"{language}_{stars[0]}-{stars[1]}")
    else:
        raise ValueError(f"Bad choice of step={step!r} and mode={mode!r}.")


def main():
    args = ArgParser(underscores_to_dashes=True).parse_args()
    args.check_args()
    extract_and_save(args.stars, args.lang, args.output, args.step, args.mode)


if __name__ == "__main__":
    main()
