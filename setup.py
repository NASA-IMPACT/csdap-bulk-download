import setuptools

setuptools.setup(
    name="csdap_bulk_download",
    version="1.0",
    author="NASA Impact",
    author_email="csdap@uah.edu",
    description="Bulk download tool for CSDAP orders.",
    install_requires=[
        "Click",
        "requests >= 2.24.0",
    ],
    entry_points={
        "console_scripts": [
            "csdap-bulk-download = csdap_bulk_download.cli:cli",
        ],
    },
)
