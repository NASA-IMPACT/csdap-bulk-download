from csdap_bulk_download.client import CsdaClient


def test_init() -> None:
    """Just a smoke test, doesn't do any auth."""
    _ = CsdaClient()
