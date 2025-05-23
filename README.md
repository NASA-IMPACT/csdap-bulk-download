# CSDA Bulk Download

TODO

## Usage

TODO

## Development

Get [uv](https://docs.astral.sh/uv/getting-started/installation/).
Then:

```sh
git clone git@github.com:NASA-IMPACT/csdap-bulk-download.git
cd csdap-bulk-download
uv sync
uv run pre-commit install
```

We use [nbstripout](https://github.com/kynan/nbstripout) to ensure that we don't check in any Earthdata credentials in our example notebook(s).
If your commit is failing, clear the notebook outputs before committing.
