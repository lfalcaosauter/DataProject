# Usa uma imagem oficial do Python, versão leve
FROM python:3.10-slim

# Define a pasta de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do projeto para dentro do contêiner
COPY . .

# Comando que será executado quando o contêiner rodar (executa os 4 scripts na sequência)
CMD ["sh", "-c", "python scripts/dados.py && python scripts/bronze.py && python scripts/silver.py && python scripts/gold.py"]