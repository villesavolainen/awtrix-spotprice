FROM python:3.9-slim-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY nordpool.py .

# Make the script executable
RUN chmod +x nordpool.py

# Run the script
CMD ["python", "nordpool.py"]