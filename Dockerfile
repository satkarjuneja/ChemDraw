FROM continuumio/miniconda3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# -----------------------------
# System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Install nauty (geng)
# -----------------------------
WORKDIR /tmp

RUN wget https://pallini.di.uniroma1.it/nauty27r1.tar.gz \
    && tar -xzf nauty27r1.tar.gz \
    && cd nauty27r1 \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && ln -sf /usr/local/bin/geng /usr/bin/geng

# HARD FAIL if geng is missing
RUN /usr/bin/geng -h >/dev/null

# -----------------------------
# Python environment
# -----------------------------
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# -----------------------------
# Expose & run
# -----------------------------
EXPOSE 5000
CMD ["python", "backend.py"]
