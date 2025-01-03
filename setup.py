import setuptools

setuptools.setup(
    name="csdap_bulk_download",
    version="1.0.1",
    description="Bulk download tool for CSDAP orders.",
    author="NASA Impact",
    author_email="support-csda@nasa.gov",
    maintainer="Anthony Lukach",
    maintainer_email="anthony@developmentseed.org",
    url="https://github.com/nasa-impact/csdap-bulk-download",
    install_requires=[
        "Click",
        "tqdm >= v4.60.0",
        "requests >= 2.24.0",
    ],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "csdap-bulk-download = csdap_bulk_download.cli:cli",
        ],
    },
)
