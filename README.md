# 🔗 URL Shortener API

A high-performance URL shortener API built with FastAPI, featuring Redis caching, rate limiting, and Docker containerization.

## Features

**Fast redirects** with Redis caching (sub-millisecond response times)
**Rate limiting** to prevent abuse (100 requests/hour per IP)
**Optional URL expiration** 
**Docker support** for easy deployment
**Comprehensive testing** with pytest

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/url` | Create a shortened URL |
| GET | `/url/{short_code}` | Get URL information |
| GET | `/go/{short_code}` | Redirect to original URL |
| DELETE | `/url/{short_code}` | Disable a URL |
| GET | `/urls` | List all URLs |



# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs