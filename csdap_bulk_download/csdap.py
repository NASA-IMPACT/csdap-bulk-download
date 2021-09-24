import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm


logger = logging.getLogger(__name__)


@dataclass
class CsdapClient:
    csdap_api_url: str

    @property
    def auth_endpoint(self) -> str:
        return f"{self.csdap_api_url}/v1/auth"

    def get_auth_token(self, username: str, password: str):
        # Get URL to EDL
        response = requests.get(
            f"{self.auth_endpoint}/",
            params={"redirect_uri": "script"},
            allow_redirects=False,
        )
        assert response.status_code in (
            302,
            307,
        ), f"Expected redirect, got {response.status_code}"
        edl_url = response.headers["Location"]
        assert urlparse(edl_url).path.startswith("/oauth/authorize")

        # Authenticate with EDL
        logger.debug("Authenticating with Earthdata Login...")
        response = requests.get(
            edl_url,
            auth=HTTPBasicAuth(username, password),
            allow_redirects=False,
        )
        response.raise_for_status()
        assert response.status_code in (
            302,
            307,
        ), f"Expected redirect, got {response.status_code}"

        querystring = parse_qs(urlparse(response.headers["Location"]).query)
        if querystring.get("error"):
            err_msg = querystring["error_msg"]
            logger.error(f"Failed to authenticate: {err_msg}")
            exit(1)

        code = querystring["code"]

        # Exchange code for token
        logger.debug("Exchanging authorization code for access token...")
        response = requests.post(f"{self.auth_endpoint}/token", data={"code": code})
        response.raise_for_status()
        token = response.json()["access_token"]
        return token

    def download_file(
        self,
        out_dir: Path,
        path: Path,
        token: str,
        **_,
    ) -> Path:
        # Prep file_dir
        file_dir = out_dir / path
        file_dir.mkdir(parents=True, exist_ok=True)

        # Download
        logger.debug("Downloading %s...", path)
        response = requests.get(
            f"{self.csdap_api_url}/v1/download/{path}",
            stream=True,
            headers={"authorization": f"Bearer {token}"},
        )
        response.raise_for_status()

        # Determine filepath
        filename = path.name
        disposition = response.headers.get("Content-Disposition")
        if disposition:
            disposition_filename = re.findall("filename=(.+)", disposition)
            if disposition_filename:
                filename = disposition_filename[0]
        filepath = file_dir / filename

        # Skip if already exists
        if filepath.exists():
            return f"Skipped, file exists at {filepath}"

        # Write to local disk
        stream = response.iter_content(chunk_size=8192)
        progress_bar = tqdm(
            stream,
            total=int(response.headers.get("content-size", 0)),
            unit="iB",
            unit_scale=True,
            desc=f"Downloading {path}",
            dynamic_ncols=True,
            leave=False
        )
        with filepath.open("wb") as f:
            for chunk in progress_bar:
                f.write(chunk)
                progress_bar.update(len(chunk))
        
        return f"Downloaded file to {filepath}"
