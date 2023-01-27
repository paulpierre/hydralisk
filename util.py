from rich.console import Console
from typing import List, Dict
from rich.table import Table
from functools import wraps
from config import CHAIN
import anyio
import json
import os
import csv
import re

console = Console()

def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def coro_wrapper():
            return await func(*args, **kwargs)

        return anyio.run(coro_wrapper)

    return wrapper


def get_chain_by_name(chain_name:str = None):

    if not chain_name:
        raise Exception("No chain name provided")

    for chain in CHAIN:
        if chain.SLUG.lower() == chain_name.lower():
            return chain

    return None


def mkdir(path=None):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def write_csv(data, filename):
    with open(filename, "w") as f:

        if isinstance(data, list):
            data = [
                {k: str(v).strip("'").replace("::jsonb", "") for k, v in row.items()}
                for row in data
            ]

        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def load_csv(filename):
    # open csv file and convert it to json  with headers as keys
    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        # convert keys to snake case lower case, make sure key is not empty
        return [
            {snake_case(k): v for k, v in row.items() if k and "@" not in k}
            for row in reader
        ]


def is_valid_address(address: str):
    return re.match(r"^0x[a-fA-F0-9]{40}$", address)


def display_table(
    data: List[Dict] = None,
    header=None,
    border=False,
    return_table=False,
    expand_table=False,
):

    if not data:
        raise Exception("No data to display")

    table = Table(
        show_header=True,
        header_style="bold cyan",
        title=header,
        show_lines=border,
        expand=expand_table,
    )
    for key in data[0].keys():
        table.add_column(key)
    for row in data:
        # convert to string
        table.add_row(*[str(v) for v in row.values()])
    if return_table:
        return table
    else:
        console.print(table)


def export_file(data: List[Dict] = None, filename: str = None):
    if not data:
        raise Exception("No data to display")
    if not filename:
        raise Exception("No filename provided")

    if filename.endswith(".csv"):
        write_csv(data, filename)
    elif filename.endswith(".json"):
        with open(filename, "w") as f:
            json.dump(data, f)
    else:
        raise Exception("Invalid file type, must end in .json or .csv")