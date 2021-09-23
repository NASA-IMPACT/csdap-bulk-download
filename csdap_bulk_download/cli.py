from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import List
import concurrent.futures
import csv
import logging

import click

from .csdap import CsdapClient
from .logger import setup_logger

import logging

logger = logging.getLogger()


@click.command()
@click.argument("input-csvs", type=click.File("r"), nargs=-1)
@click.option(
    "-o",
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
@click.option("scene_ids", "-id", "--scene_id", multiple=True, type=str.lower)
@click.option("asset_types", "-t", "--asset_type", multiple=True, type=str.lower)
@click.option("verbosity", "-v", "--verbose", count=True)
def cli(
    input_csvs: List[TextIOWrapper],
    out_dir: Path,
    csdap_api_url: str,
    username: str,
    password: str,
    verbosity: int,
    max_workers: int,
    scene_ids: List[str],
    asset_types: List[str],
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

    setup_logger(verbosity)

    csdap = CsdapClient(csdap_api_url)
    token = csdap.get_auth_token(username, password)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="CsdapDownload"
    ) as executor:
        future_to_path = {}
        for input_csv in input_csvs:
            for row in csv.DictReader(input_csv):
                path = Path(row["order_id"]) / row["scene_id"] / row["asset_type"]
                
                # Filter rows
                if scene_ids and row["scene_id"].lower() not in scene_ids:
                    logger.debug("Skipping %s, does not pass scene_id filter", path)
                    continue
                if asset_types and row["asset_type"].lower() not in asset_types:
                    logger.debug("Skipping %s, does not pass asset_type filter", path)
                    continue

                # Schedule work
                future = executor.submit(
                    csdap.download_file,
                    path=path,
                    out_dir=out_dir,
                    token=token,
                )
                future_to_path[future] = path

        # Log results
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                logger.info("%s: %s", path, future.result())
            except Exception as exc:
                logger.exception("%s generated an exception: %s" % (path, exc))
