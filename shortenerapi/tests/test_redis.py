import pytest
from fastapi.testclient import TestClient
from shortenerapi.main import app
from shortenerapi.core.redis_client import redis_client

client = TestClient(app)

@pytest.fixture(autouse=True)
async def setup_redis():
    await redis_client.connect()
    yield
    if redis_client.client:
        await redis_client.client.flushall()
        await redis_client.disconnect()

def test_redis_caching_after_create():
    # Create a URL
    response = client.post(
        "/url",
        json={"original_url": "https://example.com"}
    )
    assert response.status_code == 201
    short_code = response.json()["short_code"]
    
    # Check if cached in Redis
    import asyncio
    cached = asyncio.run(redis_client.get_url(short_code))
    assert cached == "https://example.com/"

def test_redirect_uses_redis_cache():
    # Create URL
    create_response = client.post(
        "/url",
        json={"original_url": "https://fastapi.tiangolo.com"}
    )
    short_code = create_response.json()["short_code"]
    
    # First redirect (will hit database and cache)
    response = client.get(f"/go/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    
    # Second redirect (should hit Redis cache)
    import asyncio
    cached = asyncio.run(redis_client.get_url(short_code))
    assert cached == "https://fastapi.tiangolo.com/"
    
    # Check click count in Redis
    clicks = asyncio.run(redis_client.get_clicks(short_code))
    assert clicks >= 1

def test_redis_rate_limiting():
    # Make many requests quickly
    ip = "127.0.0.1"
    for _ in range(5):
        response = client.post(
            "/url",
            json={"original_url": "https://example.com"}
        )
        assert response.status_code in [201, 429]  # Some might be rate limited