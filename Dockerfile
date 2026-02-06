FROM continuumio/miniconda3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

# -----------------------------
# System deps
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Build Nauty manually
# -----------------------------
WORKDIR /tmp
RUN wget https://pallini.di.uniroma1.it/nauty27r1.tar.gz \
    && tar -xzf nauty27r1.tar.gz \
    && cd nauty27r1 \
    && make -j$(nproc) \
    && cp geng shortg dretodot labelg /usr/local/bin/ \
    && chmod +x /usr/local/bin/geng /usr/local/bin/shortg /usr/local/bin/dretodot /usr/local/bin/labelg

# Verify geng exists
RUN /usr/local/bin/geng -h

# -----------------------------
# Python environment
# -----------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Ensure static dir exists
RUN mkdir -p /app/static

# Expose HF port
EXPOSE 7860

CMD ["python", "backend.py"]
