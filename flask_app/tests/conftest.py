import pytest
from clients import HttpClient, postgres_client
from db_models import User
from helpers import create_test_roles
from services import AccessHistoryService, CustomService
from test_data import admin_credits, url_login, url_registration, user_credits

user_service = CustomService(client=postgres_client, model=User)
access_history_service = AccessHistoryService(postgres_client)


@pytest.fixture(scope="session")
def create_roles():
    create_test_roles()
    yield


@pytest.fixture(scope="class")
def http_session(create_roles):
    with HttpClient().get_session() as session:
        yield session
    access_history_service.clear()
    user_service.clear()


@pytest.fixture
def create_user(http_session) -> dict:
    http_session.post(url_registration, json=user_credits)
    response_login = http_session.post(url_login, json=user_credits)
    access_token: str = response_login.json().get("access_token")
    refresh_token: str = response_login.json().get("refresh_token")

    yield {
        "http_session": http_session,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def create_admin(http_session) -> dict:
    # http_session.post(url_registration, json=admin_credits)
    response_login = http_session.post(url_login, json=admin_credits)
    access_token: str = response_login.json().get("access_token")
    refresh_token: str = response_login.json().get("refresh_token")

    yield {
        "http_session": http_session,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
