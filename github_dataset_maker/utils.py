from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd


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


def read_multiline_txt_file(file_path: Path | str) -> list[str]:
    """Read a multiline text file and returns a list of lines."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def save_json(repos: list, filename: Path | str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2)


def save_multiline_txt(
    file_path: Path | str, lines: list[str], append: bool = True
) -> None:
    """Write a multiline text file to the file system."""
    with open(file_path, "a" if append else "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
