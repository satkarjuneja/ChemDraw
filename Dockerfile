# Base image with conda
FROM continuumio/miniconda3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"  # ensure geng symlink is in PATH

# -----------------------------
# System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    nauty \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Symlink geng to /usr/local/bin so subprocess finds it
RUN ln -s /usr/bin/geng /usr/local/bin/geng

# -----------------------------
# Python + RDKit
# -----------------------------
RUN conda install -c conda-forge \
    python=3.10 \
    rdkit \
    -y \
    && conda clean -afy

# -----------------------------
# App setup
# -----------------------------
WORKDIR /app
COPY . /app

# Ensure static directory exists for saving PNGs
RUN mkdir -p /app/static

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose HF-required port
EXPOSE 7860

# Run Flask backend
CMD ["python", "backend.py"]
