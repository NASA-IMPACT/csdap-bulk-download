# CSDAP Bulk Download Script

## Description

Authorized users submit data requests through the Smallsat Data Explorer (SDX) for desired data scenes. Once an order is approved, users will receive a .csv file that includes download links to the ordered scenes. Each ordered scene includes a separate download link for each asset type. Depending on the number of ordered scenes and associated assets, the .csv could have many download links. This script allows users to conveniently download all files or to select a subset of files to download by filtering the .csv file.

Note: Download links can only be downloaded once. However, user downloads are logged so that if there is a failure during download (e.g., loss of internet), executing this script again will start downloading files that were not previously downloaded. 

## Required Libraries

argparse, logging, os, pandas, re, requests, tqdm

## Filter for Desired Scenes

Users can filter the .csv file by scene_id or by asset_type. This is accomplished by providing two arguments: filtercolumn and filtervalue. The two options for the filtercolumn argument is scene_id or asset_type. The second argument, filtervalue, corresponds to the desired value of the filtercolumn. For example, providing `--filtercolumn asset_type --filtervalue udm` filters the .csv by the udm asset.  

## Running the Script

1. Download the csdap_bulk_download repository to your local machine.

2. Save the data order .csv file to the same directory as the csdap_bulk_download repository. 

3. Determine if scenes will be filtered (see above).

4. Determine the name of the folder that the files will be downloaded to (default name is "Downloads"). This name should be provided as the last argument when running the script.

5. Navigate to necessary directory:  
`$python download.py --inputcsv --filtercolumn --filtervalue --downloadfolder `


