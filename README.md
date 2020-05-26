# CSDAP Bulk Download Script

## Description

Authorized users submit data requests through the Smallsat Data Explorer (SDX) for desired data scenes. Once an order is approved, users will receive a .csv file that includes download links for the ordered scenes. Each ordered scene will include a download for each asset type. Depending on the number of ordered scenes and associated assets, the .csv could have many download links. This script allows users to conveniently download all or a subset of the assets.

Note: Download links can only be downloaded once. However, downloads are logged so that if there is a failure during download (e.g., loss of internet), executing this script again start downloading files that were not previously downloaded. 

### Required Libraries

argparse, logging, os, pandas, re, requests, tqdm

## Running the Script



