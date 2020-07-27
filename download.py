#!/usr/bin/python3
"""
This is a simple script to download order assets from the CSDAP. It makes the
following assumptions:
- Python version >=3.6
- Requests module is installed (https://requests.readthedocs.io/)
- Script is called with path to Assets CSV (e.g. "python csdap.py assets.csv")
- the Assets CSV contains the following columns:
    - order_id
    - scene_id
    - asset_type
-A user has the option to filter the csv file and only download a subset of files based on scene_id or asset_type.

This script will look for Earthdata Login authentication credentials in the
following environment variables:
    - EDL_USER
    - EDL_PASS
If not found, the user will be prompted for credentials.

NOTE: a user is only granted access to download each file once.

Running the script: Arguments
- inputcsv: The is the path to the input csv file (i.e. orders.csv)
- filtercolumn (optional): This is the column in the csv file that you want to filter by.
- filtervalue (optional): This is the value in the filtercolumn that you want to filter by.
- downloadfolder (optional): The name of the folder to download the files to (default name is Order_Downloads_mmddyyyy-HHMM
"""

import argparse
import concurrent.futures
import csv
from datetime import datetime
import logging
import os
import re
import time
from time import time
import traceback
from urllib.parse import parse_qs, urlparse
from getpass import getuser, getpass

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


logger = logging.getLogger()
logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(message)s", level=logging.INFO)


CSDAP_ROOT = "https://csdap.earthdata.nasa.gov"
CSDAP_API = f"{CSDAP_ROOT}/api"
EDL_ROOT = "https://urs.earthdata.nasa.gov"

# columns expected in the input csv file
EXPECTED_COLUMNS = ("order_id", "scene_id", "asset_type")


def parse_arguments():
    """
        python download.py input.csv --filtercolumn asset_type --filtervalue udm --downloadfolder
            Parameters:
                None
            Returns:
                tuple of arguments: args.inputcsv, args.filtercolumn, args.filtervalue, args.downloadfolder

    """

    now = datetime.now()
    datetimestamp = now.strftime("%m%d%Y-%H:%M")
    default_folder_name = "Order_Downloads_" + datetimestamp
    parser = argparse.ArgumentParser(
        description="This script allows for filtering the download csv by a desired scene or asset type. URL links for the selected data downloads are returned. The expected columns are scene_id, asset_type, and links."
    )
    parser.add_argument("inputcsv", type=str,
                        help="path to the input csv file")
    parser.add_argument(
        "--filtercolumn",
        type=str,
        help="column that you want to filter on.",
        choices=["scene_id", "asset_type"],
    )
    parser.add_argument("--filtervalue", type=str, help="value to filter by")
    parser.add_argument(
        "--downloadfolder",
        type=str,
        default=default_folder_name,
        help="name of the folder to download to",
    )

    args = parser.parse_args()
    # Check either both or neither of filtercolumn and filtervalue have been passed
    if len([x for x in (args.filtercolumn, args.filtervalue) if x is not None]) == 1:
        parser.error("--filtercolumn and --filtervalue must be given together")

    return args.inputcsv, args.filtercolumn, args.filtervalue, args.downloadfolder


def filter_by(key, value, df):
    """
        Function to allow user to filter csv for desired data
            Parameters:
                key (str): column name to filter by
                value (str): value to filter by
                df (DataFrame): input dataframe
            Returns:
                df (DataFrame): filtered dataframe
    """

    return df[df[key] == value]


def file_exists(path):
    """
        Function to see if file has already been downloaded
            Parameters:
                path (str): path to check if the folder exists
            Returns:
                bool: does the path exist
    """

    return os.path.exists(path)


def create_folder_if_not_exist(folder_name):
    """
        Function to create a new folder to download links to ()
            Parameters:
                folder_name (str): name of the folder to create
            Returns:
                None
    """

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def ingest_csv(csv_file_name, filter_dict):
    """
        Function to ingest csv file and filter it.
            Parameters:
                csv_file_name (str): csv file to ingest
                filter_dict (dict): dictionary that holds filter parameters. Example {'key': filter_column, 'value': filter_value}
            Returns:
                df (DataFrame): dataframe for the ingested csv
                empty (bool): is the dataframe empty
    """

    # read the csv file
    try:
        df = pd.read_csv(csv_file_name)
    except pd.errors.EmptyDataError:
        print("The csv file was empty.")
        exit(1)
    # check if necessary columns are in the input csv file
    missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
    if not len(missing_columns) == 0:
        print(
            f"Some columns are missing in the input csv file. Missing columns are: {missing_columns}"
        )
        exit(1)
    empty = False

    # filter rows based on input condition
    if filter_dict["key"] and filter_dict["value"]:
        df = filter_by(
            df=df, key=filter_dict["key"], value=filter_dict["value"])

    if len(df) == 0:
        print(
            "Either the input csv file had zero rows or the filter returned zero rows."
        )
        empty = True
    return df, empty


def main(csv_file_name, download_folder_name, filter_dict):
    """
        Main function that drives the code.
            Parameters:
                csv_file_name (str): name of the ingested csv
                download_folder_name (str): folder to download all of the files to
                filter_dict (dict): dictionary that holds filter parameters. Example {'key': filter_column, 'value': filter_value}
            Returns:
                None
    """
    create_folder_if_not_exist(download_folder_name)

    df, empty = ingest_csv(csv_file_name, filter_dict)

    if not empty:

        os.chdir(download_folder_name)
        filtered_csv_file = df.to_csv("download_files_order.csv", index=False)


def get_edl_credentials():
    username = (
        os.environ.get("EDL_USER") or input(
            f"Username ({getuser()}): ") or getuser()
    )
    password = os.environ.get("EDL_PASS") or getpass()
    return username, password


def get_auth_token(username, password):
    CSDAP_AUTH_ENDPOINT = f"{CSDAP_API}/v1/auth"

    # Get URL to EDL
    response = requests.get(
        f"{CSDAP_AUTH_ENDPOINT}/",
        params=dict(redirect_uri="script"),
        allow_redirects=False,
    )
    assert response.status_code in (
        302,
        307,
    ), f"Expected redirect, got {response.status_code}"
    edl_url = response.headers["Location"]
    assert edl_url.startswith(f"{EDL_ROOT}/oauth/authorize")

    # Authenticate with EDL
    logger.info("Authenticating with Earthdata Login...")
    response = requests.get(
        edl_url, auth=HTTPBasicAuth(username, password), allow_redirects=False,
    )
    response.raise_for_status()
    assert response.status_code in (
        302,
        307,
    ), f"Expected redirect, got {response.status_code}"

    querystring = parse_qs(urlparse(response.headers["Location"]).query)
    if querystring.get('error'):
        err_msg = querystring['error_msg']
        logger.error(f"Failed to authenticate: {err_msg}")
        exit(1)

    code = querystring['code']

    # Exchange code for token
    logger.info("Exchanging authorization code for access token...")
    response = requests.post(
        f"{CSDAP_AUTH_ENDPOINT}/token", data=dict(code=code))
    response.raise_for_status()
    token = response.json()["access_token"]
    return token


def download_file(order_id, scene_id, asset_type, token, **kwargs):
    identifier = f"{order_id}/{scene_id}/{asset_type}"

    # Prep outpath
    outpath = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), identifier)
    os.makedirs(outpath, exist_ok=True)

    # Download
    logger.info(f"Downloading {identifier}...")
    response = requests.get(
        f"{CSDAP_API}/v1/download/{identifier}",
        stream=True,
        headers=dict(authorization=f"Bearer {token}"),
    )
    response.raise_for_status()

    # Determine filename
    filename = asset_type
    disposition = response.headers.get("Content-Disposition")
    logger.info(f'headers {response.headers}')
    if disposition:
        disposition_filename = re.findall("filename=(.+)", disposition)
        if disposition_filename:
            filename = disposition_filename[0]

    # Write to local disk
    filepath = os.path.join(outpath, filename)
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return filepath


if __name__ == "__main__":
    csv_file_name, filter_column, filter_value, download_folder_name = parse_arguments()
    main(
        csv_file_name,
        download_folder_name,
        {"key": filter_column, "value": filter_value},
    )

    start = time()
    [username, password] = get_edl_credentials()
    token = get_auth_token(username, password)

    concurrency = 5
    with open("download_files_order.csv") as csv_file:
        rows = csv.DictReader(csv_file)
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_row = {
                executor.submit(download_file, **row, token=token): row for row in rows
            }
            for future in concurrent.futures.as_completed(future_to_row):
                row = future_to_row[future]
                try:
                    logger.info(f"Wrote {future.result()}")
                except Exception as exc:
                    logger.error('%r generated an exception: %s' % (row, exc))
                    traceback.print_exc()

    logger.info(f"Time to download: {time() - start}")
