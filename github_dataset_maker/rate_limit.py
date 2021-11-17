from __future__ import annotations

import datetime
import functools
import os
import time
from typing import Any, Callable, TypeVar, cast

from dotenv import load_dotenv
from github import Github

load_dotenv()
API_TOKEN = os.environ["GITHUB_API_TOKEN"]
TCallable = TypeVar("TCallable", bound=Callable[..., Any])


def get_rate_limit() -> tuple[int, int]:
    pygithub = Github(API_TOKEN)
    rate_limit = pygithub.get_rate_limit()
    core_rate_limit = rate_limit.core.remaining
    search_rate_limit = rate_limit.search.remaining
    return core_rate_limit, search_rate_limit


def check_rate_limit():
    core_rate_limit, search_rate_limit = get_rate_limit()
    print("Core limit remaining:", core_rate_limit)
    print("Search limit remaining:", search_rate_limit)
    if search_rate_limit < 3 or core_rate_limit < 1000:
        print(
            "Sleeping a bit...",
            datetime.datetime.now().isoformat().split(".")[0].split("T")[1],
        )
        time.sleep(30)


def wait_on_rate_limits(func: TCallable) -> TCallable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_rate_limit()
        return func(*args, **kwargs)
    return cast(TCallable, wrapper)


if __name__ == "__main__":
    print(get_rate_limit())
