FROM python:3.11-slim

# Install system dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget gnupg2 ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 unzip xvfb \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -qO /tmp/google-chrome.deb \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i /tmp/google-chrome.deb || apt-get update && apt-get -f install -y && \
    rm /tmp/google-chrome.deb

# Install ChromeDriver (matching scraper version)
RUN CHROMEDRIVER_VERSION="137.0.7151.103" && \
    wget -O /tmp/chromedriver.zip \
    "https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /tmp && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy configuration
COPY config/ ./config/

# Copy source code
COPY src/ ./src/
COPY test_navigation.py ./

# Create required directories
RUN mkdir -p /app/logs /app/screenshots /app/cookies

# Copy environment file
COPY .env* ./

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/main.py"]