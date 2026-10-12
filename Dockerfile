# Use official lightweight Python image
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install basic OS utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source, frontend build, and launch scripts
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/
COPY .env.example .
COPY run.py .
COPY TECHNICAL_DESIGN_DOCUMENT.md .
COPY TECHNICAL_DESIGN_DOCUMENT.pdf .

# Ensure storage directories exist
RUN mkdir -p backend/sample_receipts backend/uploads data

# Expose default application port
EXPOSE 8000

# Default environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Launch application
CMD ["python", "run.py"]
