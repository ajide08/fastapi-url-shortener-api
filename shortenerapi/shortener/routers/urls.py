from fastapi import APIRouter, HTTPException, status
from shortenerapi.shortener.models import UrlResponse, Url
from fastapi.responses import RedirectResponse
from shortenerapi.core.database import database, url_table
from shortenerapi.core.redis_client import redis_client
from datetime import datetime, timezone
import secrets

router = APIRouter()

@router.post('/url', response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
async def create_url(url: Url):
    """
    Accepts a long URL, generates a unique short code, and saves it.
    """
    ttl_seconds = None
    if url.expires_at:
        expires_at = url.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        ttl_seconds = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl_seconds <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expires_at must be in the future",
            )

    while True:
        short_code = secrets.token_urlsafe(4)[:6]
        query = url_table.select().where(url_table.c.short_code == short_code)
        existing_url = await database.fetch_one(query)
        if existing_url is None:
            break

    query = url_table.insert().values(
        original_url=str(url.original_url),
        expires_at=url.expires_at,
        short_code=short_code,
        click_count=0,
        is_active=True
    )
    
    new_id = await database.execute(query)

    await redis_client.set_url(short_code, str(url.original_url), ttl_seconds)

    return {
        "id": new_id,
        "original_url": str(url.original_url),
        "expires_at": url.expires_at,
        "short_code": short_code,
        "click_count": 0,
        "is_active": True,
    }

@router.get('/url/{short_code}', response_model=UrlResponse, status_code=status.HTTP_200_OK)
async def get_url(short_code: str):
    cached_url = await redis_client.get_url(short_code)
    if cached_url:
        # Get click count from Redis
        clicks = await redis_client.get_clicks(short_code)
        return {
            "id": 0,  # We don't have ID from cache
            "original_url": cached_url,
            "expires_at": None,  # We don't have expiry from cache
            "short_code": short_code,
            "click_count": clicks,
            "is_active": True,
        }
    query = url_table.select().where(url_table.c.short_code == short_code)
    url = await database.fetch_one(query)
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Url not Found')
    await redis_client.set_url(short_code, url.original_url)

    return url

@router.get('/urls', response_model=list[UrlResponse], status_code=status.HTTP_200_OK)
async def get_urls():
    query = url_table.select()
    return await database.fetch_all(query)

@router.delete('/url/{short_code}')
async def delete_url(short_code: str):
    query = url_table.select().where(url_table.c.short_code == short_code)
    url = await database.fetch_one(query)
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')
    delete_query = url_table.delete().where(url_table.c.short_code == short_code)
    await database.execute(delete_query)
    await redis_client.delete_url(short_code)

    return {'msg': 'Deleted'}

@router.get('/go/{short_code}')
async def redirect_url(short_code:str):
    original_url = await redis_client.get_url(short_code)
    
    if original_url:
        # Found in Redis! Update stats
        await redis_client.increment_clicks(short_code)
        await redis_client.add_to_recent(short_code)
        
        return RedirectResponse(
            url=original_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
    query = url_table.select().where(url_table.c.short_code == short_code)
    url = await database.fetch_one(query)
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Url not Found')
    if not url.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail='Url disabled')
    update_query = url_table.update.where(url_table.c.short_code == short_code).values(click_count = url.click_count + 1)
    await database.execute(update_query)
    await redis_client.set_url(short_code, url.original_url)
    await redis_client.increment_clicks(short_code)
    await redis_client.add_to_recent(short_code)
    return RedirectResponse(
        url=str(url.original_url),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )