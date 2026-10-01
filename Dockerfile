FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the offline wheelhouse and requirements
COPY wheelhouse/ /app/wheelhouse/
COPY requirements-lock.txt /app/

# Install strictly from the offline wheelhouse
RUN pip install --no-index --no-deps --find-links=/app/wheelhouse/ -r requirements-lock.txt

# Copy the rest of the application
COPY . /app/

# Create necessary directories
RUN mkdir -p data/raw data/samples models_cache reports scratch

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit application
CMD ["streamlit", "run", "cipherlens/ui/streamlit_app.py", "--server.address=0.0.0.0"]
