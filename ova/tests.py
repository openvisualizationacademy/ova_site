def test_asgi_app_loads():
    """Verify the ASGI application (Daphne entry point) can start without errors."""
    from ova.asgi import application

    assert application is not None