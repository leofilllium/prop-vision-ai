FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostGIS, shapely, and ffmpeg (slideshow video generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose API port
EXPOSE 58000

# Run initialization and start server
ENTRYPOINT ["./entrypoint.sh"]
