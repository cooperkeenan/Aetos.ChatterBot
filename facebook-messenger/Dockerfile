FROM python:3.11-slim

# Install system dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget gnupg2 ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 unzip xvfb \
    curl procps \
    libglib2.0-0 libfontconfig1 \
    libxrender1 libxi6 libxrandr2 libxcomposite1 libxcursor1 \
    libxdamage1 libxtst6 libappindicator3-1 libatk-bridge2.0-0 \
    libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 \
    libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Testing 141.0.7390.54
RUN wget -O /tmp/chrome-linux64.zip \
    "https://storage.googleapis.com/chrome-for-testing-public/141.0.7390.54/linux64/chrome-linux64.zip" && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
    chmod +x /opt/chrome-linux64/chrome && \
    ln -sf /opt/chrome-linux64/chrome /usr/bin/google-chrome-stable && \
    ln -sf /opt/chrome-linux64/chrome /usr/bin/google-chrome && \
    rm /tmp/chrome-linux64.zip

# Install ChromeDriver 141.0.7390.54
RUN CHROMEDRIVER_VERSION="141.0.7390.54" && \
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