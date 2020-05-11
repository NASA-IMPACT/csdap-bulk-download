#!/usr/bin/env python
"""
Usage: python download.py

This script allows for filtering the download csv by a desired scene or asset type. URL links for the selected data downloads are returned.
The expected columns are scene_id, asset_type, and links.
"""

import os
import pandas as pd
import re
import requests


def filter_by(key, value, df):
    """
        Function to allow user to filter csv for desired data
    """

    return df[df[key] == value]


def file_exists(path):
    """
        Function to see if file has already been downloaded
    """

    return os.path.exists(path)


def create_folder_if_not_exist(folder_name):
    """
        Function to create a new folder to download links to ()
    """

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def download(link, file_name, folder_name):
    """
        Function to download link to desired data
    """

    path = f"{folder_name}/{file_name}"
    if file_exists(path):
        print(f"File {path} not downloaded because it already exist. The link is {link}")
        return
    create_folder_if_not_exist(folder_name)
    try:
        r = requests.get(link, allow_redirects=True)
        open(os.path.join(folder_name, file_name), 'wb').write(r.content)
        print(f"Link downloaded to {path}")
    except Exception as e:
        print(e)


def extract_file_name(row):
    """
        Function to extract file name from S3 link.
    """

    return re.search('(PS.*)\?', row["link"]).group(0)[:-1]


def download_row(row, download_folder_name):
    """
        Function to download file from row in csv.
    """

    download(link="http://google.com/favicon.ico",
             file_name=row['file_name'], folder_name=os.path.join(download_folder_name, row['folder_name']))


def ingest_csv(csv_file_name, filter_dict):
    """
        Function to ingest csv file and filter it.
    """

    df = pd.read_csv(csv_file_name)
    df = filter_by(df=df, key=filter_dict['key'], value=filter_dict['value'])

    return df


def create_additional_columns(df):
    """
        Function to create additional columns for download.
    """

    df["scene_type"] = df.scene_id.str.split("-").str[0]
    df['file_name'] = df.apply(lambda row: extract_file_name(row), axis=1)
    df["folder_name"] = df.apply(lambda row: row['file_name'].rsplit('/', 1)[0], axis=1)
    df["file_name"] = df.apply(lambda row: row['file_name'].rsplit('/', 1)[1], axis=1)

    return df


def main(csv_file_name, download_folder_name, filter_dict):
    """
        Main function that drives the code.
    """

    create_folder_if_not_exist(download_folder_name)

    df = ingest_csv(csv_file_name, filter_dict)
    create_additional_columns(df)

    #    download files from csv one row at a time
    df.apply(lambda row: download_row(row, download_folder_name), axis=1)

    return df


if __name__ == '__main__':
    main("leancsv.csv", "downloads", {'key': 'asset_type', 'value': 'udm'})
