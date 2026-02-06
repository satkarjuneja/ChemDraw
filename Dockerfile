FROM continuumio/miniconda3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System deps (nauty / geng)
RUN apt-get update && apt-get install -y \
    nauty \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install RDKit properly
RUN conda install -c conda-forge \
    rdkit \
    python=3.10 \
    -y \
    && conda clean -afy

WORKDIR /app

# Copy everything
COPY . /app

# Install remaining Python deps
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["python", "backend.py"]
