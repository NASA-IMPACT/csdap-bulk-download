from csda_client.client import CsdaClient


def test_init() -> None:
    """Just a smoke test, doesn't do any auth."""
    _ = CsdaClient()
