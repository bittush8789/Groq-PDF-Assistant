# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user
RUN groupadd -r streamlit && useradd -r -g streamlit streamlit
RUN mkdir -p /app/uploads /app/vector_store_db && \
    chown -R streamlit:streamlit /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/streamlit/.local
ENV PATH=/home/streamlit/.local/bin:$PATH

# Copy application code
COPY --chown=streamlit:streamlit . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER streamlit

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
