from pydantic import BaseModel, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional

class Url(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None

class UrlResponse(Url):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    click_count: int
    is_active : bool

class UrlStats(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    ttl_seconds: Optional[int] = None
    cached: bool = True