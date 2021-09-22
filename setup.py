import setuptools

setuptools.setup(
    name="csdap_bulk_download",
    version="1.0",
    author="NASA Impact",
    description="Bulk download tool for CSDAP orders.",
    install_requires=[
        "Click",
        # "pandas >= 1.0.5",
        "requests >= 2.24.0",
    ],
    entry_points={
        "console_scripts": [
            "csdap-bulk-download = csdap_bulk_download.cli:cli",
        ],
    },
)