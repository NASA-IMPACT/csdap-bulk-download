#!/usr/bin/env python
"""
Usage: python download.py

This script allows for filtering the download csv by a desired scene or asset type. URL links for the selected data downloads are returned.
The expected columns are scene_id, asset_type, and links.
"""

import argparse
import logging
import os
import pandas as pd
import re
import requests

from tqdm import tqdm

logging.basicConfig(format='%(asctime)s %(message)s',
                    filename='download.log', level=logging.INFO)

# columns expected in the input csv file
EXPECTED_COLUMNS = ("scene_id", "asset_type", "link")


def parse_arguments():
    """
        python download.py input.csv --filtercolumn asset_type --filtervalue udm --downloadfolder downloads
            Parameters:
                None
            Returns:
                tuple of arguments: args.inputcsv, args.filtercolumn, args.filtervalue, args.downloadfolder

    """

    parser = argparse.ArgumentParser(
        description='This script allows for filtering the download csv by a desired scene or asset type. URL links for the selected data downloads are returned. The expected columns are scene_id, asset_type, and links.')
    parser.add_argument('inputcsv', type=str,
                        help='path to the input csv file')
    parser.add_argument('--filtercolumn', type=str,
                        help='column that you want to filter on.', choices=['scene_id', 'asset_type'])
    parser.add_argument('--filtervalue', type=str,
                        help='value to filter by')
    parser.add_argument('--downloadfolder', type=str, default="downloads",
                        help='name of the folder to download to')

    args = parser.parse_args()
    # Check either both or neither of filtercolumn and filtervalue have been passed
    if len([x for x in (args.filtercolumn, args.filtervalue) if x is not None]) == 1:
        parser.error('--filtercolumn and --filtervalue must be given together')

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


def download(link, file_name, folder_name):
    """
        Function to download link to desired data
            Parameters:
                link (str): link to file being downloaded
                file_name (str): filename for the downloaded file              
                folder_name (str): folder to put the file in
            Returns:
                None
    """

    path = f"{folder_name}/{file_name}"
    if file_exists(path):
        logging.info(
            f"File {path} not downloaded because it already exists. The link is {link}")
        return
    create_folder_if_not_exist(folder_name)

    r = requests.get(link, allow_redirects=True)
    open(os.path.join(folder_name, file_name), 'wb').write(r.content)
    logging.info(f"Link downloaded to {path}")


def extract_file_name(row):
    """
        Function to extract file name from S3 link.
            Parameters:
                row (DataFrame row): one row from the csv file
            Returns:
                str: filename of the file to be downloaded
    """

    return re.search('(PS.*)\?', row["link"]).group(0)[:-1]


def download_row(row, download_folder_name):
    """
        Function to download file from row in csv.
            Parameters:
                row (DataFrame row): one row from the csv file
                download_folder_name (str): name of the folder to download the file to
            Returns:
                None
    """

    download(link="ht://google.com/favicon.ico",
             file_name=row['file_name'], folder_name=os.path.join(download_folder_name, row['folder_name']))


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
            f"Some columns are missing in the input csv file. Missing columns are: {missing_columns}")
        exit(1)
    empty = False

    # filter rows based on input condition
    if filter_dict['key'] and filter_dict['value']:
        df = filter_by(
            df=df, key=filter_dict['key'], value=filter_dict['value'])

    if len(df) == 0:
        print("Either the input csv file had zero rows or the filter returned zero rows.")
        empty = True
    return df, empty


def create_additional_columns(df):
    """
        Function to create additional columns for download.
            Parameters:
                df (DataFrame): input dataframe
            Returns:
                df (DataFrame): dataframe with additional columns
    """

    df["scene_type"] = df.scene_id.str.split("-").str[0]
    df["file_name"] = df.apply(lambda row: extract_file_name(row), axis=1)
    df["folder_name"] = df.apply(
        lambda row: row["file_name"].rsplit('/', 1)[0], axis=1)
    df["file_name"] = df.apply(
        lambda row: row["file_name"].rsplit('/', 1)[1], axis=1)

    return df


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
        create_additional_columns(df)
        tqdm.pandas()
        #    download files from csv one row at a time
        df.progress_apply(lambda row: download_row(
            row, download_folder_name), axis=1)


if __name__ == '__main__':
    csv_file_name, filter_column, filter_value, download_folder_name = parse_arguments()
    main(csv_file_name, download_folder_name, {
         'key': filter_column, 'value': filter_value})
