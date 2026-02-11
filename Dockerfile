# Usamos Python ligero
FROM python:3.10-slim

# Evitar archivos basura de Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para MySQL y compilación
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libcairo2-dev \
    libjpeg-dev \
    libgif-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código del proyecto
COPY . /app/

# Comando para arrancar (Ajusta 'NOMBRE_DE_TU_PROYECTO' abajo)
# Gunicorn correrá en el puerto 8000 interno del n", "--bind", "0.0.0.0:8000"]
CMD ["gunicorn", "appPrincipal.wsgi:application", "--bind", "0.0.0.0:8000"]
