from fastapi import FastAPI, HTTPException, Request
from shortenerapi.shortener.routers.urls import router as url_router
from contextlib import asynccontextmanager
from shortenerapi.core.database import database
from shortenerapi.core.config import get_settings
from shortenerapi.core.redis_client import redis_client
from fastapi.responses import JSONResponse

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await redis_client.connect()
    yield
    await database.disconnect()    
    await redis_client.disconnect()

app = FastAPI(lifespan=lifespan)



@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    is_allowed = await redis_client.check_rate_limit(
        client_ip,
        limit=100, 
        window=3600  
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    response = await call_next(request)
    return response


app.include_router(url_router)