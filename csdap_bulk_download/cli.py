from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import List
import concurrent.futures
import csv
import logging

import click
from tqdm.contrib.logging import logging_redirect_tqdm

from .csdap import CsdapClient
from .logger import setup_logger


logger = logging.getLogger(__name__)


@click.command()
@click.argument("input-csvs", type=click.File("r"), nargs=-1, required=True)
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
    "-u",
    "--edl-username",
    envvar="EDL_USER",
    prompt="Earthdata Login username",
    show_default="Environment variable 'EDL_USER' or prompt",
    help="Earthdata Login username",
)
@click.option(
    "password",
    "-pw",
    "--edl-password",
    envvar="EDL_PASS",
    prompt="Earthdata Login password",
    hide_input=True,
    show_default="Environment variable 'EDL_PASS' or prompt",
    help="Earthdata Login password",
)
@click.option(
    "-c",
    "--concurrency",
    type=int,
    show_default="Number of processors on the machine, multiplied by 5",
    help="Number of concurrent downloads",
)
@click.option(
    "scene_ids",
    "-id",
    "--scene_id",
    multiple=True,
    type=str.lower,
    help="Filter by scene_ids",
)
@click.option(
    "asset_types",
    "-t",
    "--asset_type",
    multiple=True,
    type=str.lower,
    help="Filter by asset_type",
)
@click.option("verbosity", "-v", "--verbose", count=True)
def cli(
    input_csvs: List[TextIOWrapper],
    out_dir: Path,
    csdap_api_url: str,
    username: str,
    password: str,
    verbosity: int,
    concurrency: int,
    scene_ids: List[str],
    asset_types: List[str],
):
    """
    The CSDAP Bulk Download tool intends to make it easy to download many
    assets from an order placed within the CSDAP system.

    \b
    The Assets CSV must contain a header row with the following columns:
      - collection_id
      - scene_id
      - asset_type

    A user has the option to filter the csv file and only download a subset
    of files based on scene_id or asset_type.

    Note that a user is only granted access to download each file once.

    For more information on CSDAP, please visit https://csdap.earthdata.nasa.gov.
    For support, contact csdap@uah.edu.
    """

    setup_logger(verbosity)

    csdap = CsdapClient(csdap_api_url)
    token = csdap.get_auth_token(username, password)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency, thread_name_prefix="CsdapDownload"
    ) as executor, logging_redirect_tqdm():

        logger.debug(
            "Creating threadpool with max_workers of %s", executor._max_workers
        )
        future_to_path = {}

        def log_results(future):
            path = future_to_path.pop(future)
            try:
                logger.info("%s: %s", path, future.result())
            except Exception as exc:
                if verbosity:
                    logger.exception("%s generated an exception: %s" % (path, exc))
                else:
                    logger.warn("%s: Failed to download", path)

        for input_csv in input_csvs:
            api_version = 2
            for row in csv.DictReader(input_csv):
                if "order_id" in row and api_version == 2:
                    logger.warn("Detected legacy CSV.")
                    api_version = 1

                base = Path(
                    row["order_id"] if api_version == 1 else row["collection_id"]
                )
                path = base / row["scene_id"] / row["asset_type"]

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
                    endpoint_version=api_version,
                )
                future_to_path[future] = path
                future.add_done_callback(log_results)

                # To avoid the memory overhead of scheduling the entire CSV as futures,
                # we wait will for some futures to complete before scheduling more
                if len(future_to_path) >= 2 * executor._max_workers:
                    logger.debug(
                        "Waiting for some downloads to finish before continuing to "
                        "process CSV rows..."
                    )
                    concurrent.futures.wait(
                        future_to_path, return_when=concurrent.futures.FIRST_COMPLETED
                    )

        # Log outstanding futures
        logger.debug(
            "All CSVs processed, waiting for remaining %s downloads to complete",
            len(future_to_path),
        )
        concurrent.futures.wait(
            future_to_path, return_when=concurrent.futures.ALL_COMPLETED
        )

        click.echo("Complete.")
