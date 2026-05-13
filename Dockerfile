FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    aircrack-ng \
    iw \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY deauther.py .

# Run the TUI
ENTRYPOINT ["python", "deauther.py"]
