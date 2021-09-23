import setuptools

setuptools.setup(
    name="csdap_bulk_download",
    version="1.0",
    description="Bulk download tool for CSDAP orders.",
    author="NASA Impact",
    author_email="csdap@uah.edu",
    maintainer="Anthony Lukach",
    maintainer_email="anthony@developmentseed.org",
    url="https://github.com/nasa-impact/csdap-bulk-download",
    install_requires=[
        "Click",
        "requests >= 2.24.0",
    ],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "csdap-bulk-download = csdap_bulk_download.cli:cli",
        ],
    },
)
