FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY cogs/ ./cogs/
COPY services/ ./services/

# Run the bot
CMD ["python", "bot.py"]
