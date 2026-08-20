# 1. Create the base environment
FROM python:3.11-slim

# 2. Set up a work directory
WORKDIR /code

# 3. Install system dependencies (needed for some packages)

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy the dependency list
COPY requirements.txt .

# 5. Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the code
COPY . .

# 7. Run the application
CMD ["uvicorn", "shortenerapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
