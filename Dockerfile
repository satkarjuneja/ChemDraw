# Base image
FROM continuumio/miniconda3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

# -----------------------------
# System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Build Nauty manually (geng etc.)
# -----------------------------
WORKDIR /tmp
RUN wget https://pallini.di.uniroma1.it/nauty27r1.tar.gz \
    && tar -xzf nauty27r1.tar.gz \
    && cd nauty27r1 \
    && make -j$(nproc) \
    && cp geng shortg dretodot labelg /usr/local/bin/ \
    && chmod +x /usr/local/bin/geng /usr/local/bin/shortg /usr/local/bin/dretodot /usr/local/bin/labelg

# Verify geng works
RUN /usr/local/bin/geng -h

# -----------------------------
# Python + app setup
# -----------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure static directory exists for saving PNGs
RUN mkdir -p /app/static

# Expose HF Spaces required port
EXPOSE 7860

# Run Flask backend
CMD ["python", "backend.py"]
