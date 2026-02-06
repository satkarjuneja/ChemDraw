FROM continuumio/miniconda3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# -----------------------------
# System dependencies (nauty / geng)
# -----------------------------
RUN apt-get update && apt-get install -y \
    nauty \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Ensure geng is on PATH (nauty installs it in /usr/bin)
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

# Ensure runtime-generated directories exist
RUN mkdir -p /app/static

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face requires port 7860
EXPOSE 7860

# Run Flask backend
CMD ["python", "backend.py"]
