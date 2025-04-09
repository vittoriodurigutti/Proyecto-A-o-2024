# Dockerfile para 02_FRONTEND
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Copiar y instalar dependencias
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer el puerto configurado (5001 en este ejemplo)
EXPOSE 5001

CMD ["python", "app.py"]
