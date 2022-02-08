import logging
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

from .exceptions import AuthError


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
        if response.status_code not in (302, 307):
            raise AuthError(
                f"Expected API to respond with a redirect, got {response.status_code}"
            )

        edl_url = response.headers.get("Location", "")
        redirect_path = urlparse(edl_url).path
        if not redirect_path.startswith("/oauth/authorize"):
            raise AuthError(
                f"Expected redirect to /oauth/authorize, got {redirect_path}"
            )

        # Authenticate with EDL
        logger.debug("Authenticating with Earthdata Login...")
        response = requests.get(
            edl_url,
            auth=HTTPBasicAuth(username, password),
            allow_redirects=False,
        )
        if not response.ok:
            raise AuthError(
                "\n".join(
                    [
                        "Failed to authenticate with Earthdata Login.",
                        f"Response from server:",
                        textwrap.indent(response.text.strip(), prefix=" " * 4),
                        "HINT: check username and password.",
                    ]
                )
            )

        if response.status_code not in (302, 307):
            raise AuthError(
                f"Expected Earthdata Login to respond with a redirect, got {response.status_code}"
            )

        querystring = parse_qs(urlparse(response.headers["Location"]).query) 
        if querystring.get("error") and response.status_code == 302 and response.text.find('resolution_url'):
            start = response.text.find('resolution_url')+len('resolution_url')+1
            end = response.text.find('\"', start)
            raise AuthError(
                "\n".join(
                    [
                       "Authorization required for this application, please authorize by visiting the resolution url",
                       response.text[start:end],
                    ]
                )
            )
            
        if querystring.get("error"):
            raise AuthError(querystring["error_msg"])

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
        endpoint_version: int
        **_,
    ) -> Path:
        # Prep file_dir
        file_dir = out_dir / path
        file_dir.mkdir(parents=True, exist_ok=True)

        # Download
        logger.debug("Downloading %s...", path)
        base_path = f"v{endpoint_version}/download"
        response = requests.get(
            f"{self.csdap_api_url}/{base_path}/{path}",
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
            leave=False,
        )
        with filepath.open("wb") as f:
            for chunk in progress_bar:
                f.write(chunk)
                progress_bar.update(len(chunk))

        return f"Downloaded file to {filepath}"
