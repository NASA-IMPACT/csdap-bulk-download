# CSDAP Bulk Download Script

## Description

Authorized users submit data requests through the Smallsat Data Explorer (SDX) for desired data scenes. Once an order is approved, users will receive a .csv file that includes download links to the ordered scenes. Each ordered scene includes a separate download link for each asset type. Depending on the number of ordered scenes and associated assets, the .csv could have many download links. This script allows users to conveniently download all files or to select a subset of files to download by filtering the .csv file.

Note: Download links can only be downloaded once. However, user downloads are logged so that if there is a failure during download (e.g., loss of internet), executing this script again will start downloading files that were not previously downloaded. 

## Required Libraries

argparse, csv, datetime, getpass, logging, os, pandas, re, requests, requests.auth, sys, time, tqdm, urlib.parse

## Arguments

1. inputcsv - This is the path to the input csv file.

2. filtercolumn - This is the column in the csv file that you want to filter by.

3. filtervalue - This is the value in the filtercolumn that you want to filter by.

4. downloadfolder - The name of the folder to download the files to.

## Filter for Desired Scenes

Users can filter the .csv file by scene_id or by asset_type. This is accomplished by providing two arguments: filtercolumn and filtervalue. The two options for the filtercolumn argument is scene_id or asset_type. The second argument, filtervalue, corresponds to the desired value of the filtercolumn. For example, providing `--filtercolumn asset_type --filtervalue udm` filters the .csv by the udm asset.  

## Running the Script

1. Download the csdap_bulk_download repository to your local machine.

2. Determine if scenes will be filtered (see above). Note this is arguments two and three.

3. Determine the name of the folder that the files will be downloaded to (default name is *Order_Downloads_mmddyyyy-HH:MM*  <sup id="a1">[1](#f1)</sup> ). 

4. Save the data order.csv file to the same directory as the csdap_bulk_download repository. This argument must be the last argument.


## Examples

1. If a user wishes to filter columns with asset_type:

`$python download.py --filtercolumn asset_type --filtervalue basic_analytic_dn  orders.csv `

This will download all files with *asset_type: basic_analytic_dn* and save in a default download folder name *Order_Downloads_mmddyyyy-HH:MM*


2. If a user wishes to filter columns with asset_type, and wishes to save output in a specific folder:

`$python download.py --filtercolumn asset_type --filtervalue basic_analytic_dn  --downloadfolder my_download_folder orders.csv `

This will download all files with *asset_type: basic_analytic_dn* and save in a folder *my_download_folder*





<b id="f1">1</b> mm, dd, yyyy, HH and MM stand for current month, date, year, hour and minute respectively. [↩](#a1)
