FROM python:3.12-slim

WORKDIR /app

# Dependencias de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# HuggingFace cache dentro del container (se cachea entre restarts)
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p /app/.cache/huggingface

# Puerto que Railway espera
EXPOSE 8000

CMD ["python", "main.py"]
