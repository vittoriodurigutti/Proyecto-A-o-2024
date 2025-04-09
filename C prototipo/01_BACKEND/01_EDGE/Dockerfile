FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia y instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Expone el puerto donde corre la API (por ejemplo, 5000)
EXPOSE 5000

# Define el comando de inicio (puede ser flask run o gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
