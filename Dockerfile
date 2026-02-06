# Base image with conda
FROM continuumio/miniconda3:latest

# -----------------------------
# Environment
# -----------------------------
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
# Ensure geng symlink is in PATH for subprocess
ENV PATH="/usr/local/bin:$PATH"

# -----------------------------
# System dependencies (nauty / geng)
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

# Expose Hugging Face-required port
EXPOSE 7860

# Run Flask backend
CMD ["python", "backend.py"]
