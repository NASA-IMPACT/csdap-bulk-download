# CSDAP Bulk Download Script

Authorized users submit data requests through the Smallsat Data Explorer (SDX) for desired data scenes. Once an order is approved, users will receive a .csv file that includes download links to the ordered scenes. Each ordered scene includes a separate download link for each asset type. Depending on the number of ordered scenes and associated assets, the .csv could have many download links. This script allows users to conveniently download all files or to select a subset of files to download by filtering the .csv file.

Note: Download links can only be downloaded once. However, user downloads are logged so that if there is a failure during download (e.g., loss of internet), executing this script again will start downloading files that were not previously downloaded.

![Example usage](./.docs/example.svg)

## Installation

```sh
pip3 install --user https://github.com/NASA-IMPACT/csdap-bulk-download/archive/main.zip
```

_Note:_ Keep an eye out for a warning from `pip` along the lines of this:

    WARNING: The script csdap-bulk-download is installed in '/Users/username/Library/Python/3.8/bin' which is not on PATH.
    Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.

If you encounter this issue, you will likely need to ensure that the directory mentioned is available on your path. [See here](https://superuser.com/questions/1372793/the-script-is-installed-in-directory-which-is-not-path) for techniques on resolving this issue.

## Development

Install into a virtual environment:

```sh
pip install -e .
```

### Formatting & Linting

To maintain common code style, please format and lint all code contributions:

```sh
pip3 install -r requirements-dev.txt
black csdap_bulk_download  # Format code
flake8  # Lint code
```
