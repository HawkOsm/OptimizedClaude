import ocl


def test_smoke() -> None:
    assert ocl.main() is None
