from __future__ import annotations

import logging
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

from requests import Response, Session
from requests.auth import AuthBase, HTTPBasicAuth

from .exceptions import AuthError

logger = logging.getLogger(__name__)

METHOD = Literal["GET"] | Literal["POST"]

API_URL_STAGING = "https://csdap-staging.ds.io/api"
API_URL_PRODUCTION = "https://csdap.earthdata.nasa.gov/api"


class CsdaClient:
    @classmethod
    def open(
        cls, username: str, password: str, api_url: str = API_URL_STAGING
    ) -> CsdaClient:
        """Opens a logged-in CSDA client."""
        client = CsdaClient(api_url)
        client.login(username, password)
        return client

    def __init__(self, api_url: str = API_URL_STAGING) -> None:
        """Creates a new, un-logged-in CSDA client.

        Use `login` to get an auth token.
        """
        self.session = Session()
        self.api_url = api_url

    def request_auth(
        self,
        path: str,
        method: METHOD,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        allow_redirects: bool = True,
    ) -> Response:
        """Sends a request to an auth endpoint."""
        return self.request(
            f"/v1/auth/{path.lstrip('/')}",
            method,
            params=params,
            data=data,
            allow_redirects=allow_redirects,
        )

    def request(
        self,
        path: str,
        method: METHOD,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        allow_redirects: bool = True,
        auth: AuthBase | None = None,
    ) -> Response:
        """Sends a request.

        This is useful to re-use an auth token, e.g. retrieved via `CsdaClient.login()`.
        """
        url = self.api_url.rstrip("/") + "/" + path.lstrip("/")
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            allow_redirects=allow_redirects,
            auth=auth,
        )
        response.raise_for_status()
        return response

    def login(self, username: str, password: str) -> None:
        """Log in this client with an Earthdata username and password.

        The retrieved token is saved in the session headers.

        Needless to say, you shouldn't be saving your username or password in code.
        """
        response = self.request_auth(
            "/",
            method="GET",
            params={"redirect_uri": self.api_url},
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

        logger.debug("Authenticating with Earthdata Login...")
        response = self.session.request(
            url=edl_url,
            method="GET",
            auth=HTTPBasicAuth(username, password),
            allow_redirects=False,
        )
        if response.status_code not in (302, 307):
            raise AuthError(
                "Expected Earthdata Login to respond with a redirect, "
                f"got {response.status_code}"
            )

        querystring = parse_qs(urlparse(response.headers["Location"]).query)
        if (
            querystring.get("error")
            and response.status_code == 302
            and "resolution_url" in response.text
        ):
            start = response.text.find("resolution_url") + len("resolution_url") + 1
            end = response.text.find('"', start)
            raise AuthError(
                "\n".join(
                    [
                        "Authorization required for this application,",
                        "please authorize by visiting the resolution url",
                        response.text[start:end],
                    ]
                )
            )

        if querystring.get("error"):
            raise AuthError(querystring["error_msg"])

        logger.debug("Exchanging authorization code for access token...")
        code = querystring["code"]
        response = self.request_auth("/token", method="POST", data={"code": code})
        token = response.json()["access_token"]

        self.session.headers["Authorization"] = f"Bearer: {token}"
