echo "Iniciando MITRE Mapper API com Ollama..."

echo "Iniciando serviço Ollama..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

echo "Aguardando Ollama ficar disponível..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama está disponível"
        break
    fi
    echo "   Tentativa $i/30..."
    sleep 2
done

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Erro: Ollama não conseguiu iniciar"
    cat /tmp/ollama.log
    exit 1
fi

MODEL_NAME="${OLLAMA_MODEL:-llama3.2:1b}"
echo "Verificando modelo $MODEL_NAME..."

if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "Baixando modelo $MODEL_NAME (isso pode demorar)..."
    ollama pull "$MODEL_NAME"
    if [ $? -eq 0 ]; then
        echo "Modelo $MODEL_NAME baixado com sucesso"
    else
        echo "Aviso: Falha ao baixar modelo $MODEL_NAME"
        echo "API funcionará sem LLM"
    fi
else
    echo "Modelo $MODEL_NAME já disponível"
fi

echo "Iniciando aplicação Python..."
python startup.py