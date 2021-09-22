from concurrent.futures import thread
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from queue import Queue
import concurrent.futures
import csv
import logging

import click

from .csdap import CsdapClient
from .logger import setup_logger

import logging

logger = logging.getLogger()


def run_sleep():
    import requests

    logger.info("Running")
    response = requests.get("https://httpbin.org/delay/5")
    logger.info("Done")
    return "Done!"


@click.command()
@click.argument("input-csv", type=click.File("r"), nargs=1)
@click.option(
    "--out-dir",
    type=click.Path(file_okay=False, writable=True, resolve_path=True, path_type=Path),
    default=lambda: f"Order_Downloads_{datetime.now().strftime('%Y-%m-%d-%H%M')}",
    show_default=f"Order_Downloads_{datetime.now().strftime('%Y-%m-%d-%H%M')}",
)
@click.option(
    "--csdap-api-url",
    type=str,
    default="https://csdap.earthdata.nasa.gov/api",
    show_default=True,
)
@click.option(
    "username",
    "--edl-username",
    envvar="EDL_USER",
    prompt=True,
    show_default="Environment variable 'EDL_USER' or prompt",
)
@click.option(
    "password",
    "--edl-password",
    envvar="EDL_PASS",
    prompt=True,
    hide_input=True,
    show_default="Environment variable 'EDL_PASS' or prompt",
)
@click.option(
    "-w",
    "--max-workers",
    type=int,
    show_default="Number of processors on the machine, multiplied by 5",
)
@click.option("-v", "--verbose", count=True)
def cli(
    input_csv: TextIOWrapper,
    out_dir: Path,
    csdap_api_url: str,
    username: str,
    password: str,
    verbose: int,
    max_workers: int,
):
    """
    This is a simple script to download order assets from the CSDAP. It makes the
    following assumptions:

    - the Assets CSV contains the following columns:
        - order_id
        - scene_id
        - asset_type
    -A user has the option to filter the csv file and only download a subset of files based on scene_id or asset_type.

    NOTE: a user is only granted access to download each file once.

    Running the script: Arguments
    - filtercolumn (optional): This is the column in the csv file that you want to filter by.
    - filtervalue (optional): This is the value in the filtercolumn that you want to filter by.
    """

    setup_logger(verbose)

    csdap = CsdapClient(csdap_api_url)
    token = csdap.get_auth_token(username, password)
    click.echo(token)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="CsdapDownload"
    ) as executor:
        future_to_row = {
            executor.submit(csdap.download_file, **row, out_dir=out_dir, token=token): row
            for row in csv.DictReader(input_csv)
        }

        for future in concurrent.futures.as_completed(future_to_row):
            row = future_to_row[future]
            try:
                logger.info(f"Wrote {future.result()}")
            except Exception as exc:
                logger.exception("%r generated an exception: %s" % (row, exc))
