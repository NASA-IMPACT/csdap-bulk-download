import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from requests.auth import HTTPBasicAuth
from requests.models import Response


logger = logging.getLogger()


def _follow_redirects(response: Response):
    print(response, response.headers, )
    response.raise_for_status()
    if response.status_code in [301, 302, 307]:
        return _follow_redirects(
            requests.get(
                response.headers["Location"], stream=True, allow_redirects=False
            )
        )
    return response


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
        order_id: int,
        scene_id: str,
        asset_type: str,
        token: str,
        **_,
    ) -> Path:
        identifier = f"{order_id}/{scene_id}/{asset_type}"

        # Prep file_dir
        file_dir = out_dir / identifier
        file_dir.mkdir(parents=True, exist_ok=True)

        # Download
        logger.debug(f"Downloading {identifier}...")
        response = _follow_redirects(
            requests.get(
                f"{self.csdap_api_url}/v1/download/{identifier}",
                stream=True,
                headers={"authorization": f"Bearer {token}"},
                allow_redirects=False,
            )
        )

        # Determine filepath
        filename = asset_type
        logger.debug(f"headers {response.headers}")
        disposition = response.headers.get("Content-Disposition")
        if disposition:
            disposition_filename = re.findall("filename=(.+)", disposition)
            if disposition_filename:
                filename = disposition_filename[0]
        filepath = file_dir / filename

        # Skip if already exists
        if filepath.exists():
            logger.warn("File at %s already exists, skipping...", filepath)
            return filepath

        # Write to local disk
        with filepath.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
