from tanks.dependencies import get_session, get_settings


def test_get_settings():
    assert get_settings()


def test_get_session():
    assert get_session()
