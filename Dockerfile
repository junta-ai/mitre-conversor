# Dockerfile para produção
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema e Ollama
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Instalar Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Tornar script executável
RUN chmod +x start-with-ollama.sh

# Expor portas (8080 para API, 11434 para Ollama)
EXPOSE 8080 11434

# Comando para iniciar a aplicação com Ollama
CMD ["./start-with-ollama.sh"]