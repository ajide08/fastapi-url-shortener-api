import pytest
from fastapi.testclient import TestClient
from shortenerapi.main import app

from shortenerapi.core.database import database


@pytest.fixture(autouse=True)
def clear_url_table():
    url_table.clear()
    yield
    url_table.clear()


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_create_url(client):
    response = client.post(
        "/url",
        json={
            "original_url": "https://example.com"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://example.com/"
    assert "short_code" in data
    assert data["click_count"] == 0
    assert data["is_active"] is True


def test_get_url(client):
    create_response = client.post(
        "/url",
        json={
            "original_url": "https://example.com"
        },
    )
    short_code = create_response.json()["short_code"]
    response = client.get(f"/url/{short_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == short_code
    assert data["original_url"] == "https://example.com/"


def test_get_nonexistent_url(client):
    response = client.get("/url/doesnotexist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Url not Found"

def test_list_urls(client):
    client.post(
        "/url",
        json={"original_url": "https://example.com"},
    )
    client.post(
        "/url",
        json={"original_url": "https://github.com"},
    )
    response = client.get("/urls")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["original_url"] == "https://example.com/"
    assert data[1]["original_url"] == "https://github.com/"


def test_redirect_url(client):
    create_response = client.post(
        "/url",
        json={
            "original_url": "https://example.com"
        },
    )
    short_code = create_response.json()["short_code"]
    response = client.get(
        f"/go/{short_code}",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"
    url_response = client.get(f"/url/{short_code}")

    assert url_response.json()["click_count"] == 1


def test_redirect_increments_click_count(client):
    create_response = client.post(
        "/url",
        json={
            "original_url": "https://example.com"
        },
    )
    short_code = create_response.json()["short_code"]
    client.get(
        f"/go/{short_code}",
        follow_redirects=False,
    )
    client.get(
        f"/go/{short_code}",
        follow_redirects=False,
    )
    client.get(
        f"/go/{short_code}",
        follow_redirects=False,
    )
    assert url_table[short_code].click_count == 3


def test_disabled_url_cannot_redirect(client):
    create_response = client.post(
        "/url",
        json={
            "original_url": "https://example.com"
        },
    )
    short_code = create_response.json()["short_code"]
    client.delete(f"/url/{short_code}")
    response = client.get(
        f"/go/{short_code}",
        follow_redirects=False,
    )
    assert response.status_code == 410
    assert response.json()["detail"] == "Url disabled"

def test_invalid_url(client):
    response = client.post(
        "/url",
        json={
            "original_url": "not-a-url"
        },
    )
    assert response.status_code == 422


def test_redirect_nonexistent_url(client):
    response = client.get(
        "/go/doesnotexist",
        follow_redirects=False,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Url not Found"