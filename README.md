# Analisador de Relatórios Financeiros

API em FastAPI para receber PDFs financeiros, extrair texto, responder perguntas em linguagem natural e gerar análises estruturadas.

## Sprint 1
- Upload de PDF
- Extração de texto com `pdfplumber`
- Validação de tipo e tamanho
- Testes com `pytest`

## Sprint 2
- Integração com a API da OpenAI
- Endpoint `POST /ask` com `document_id` e `question`
- Cache simples do texto do documento em memória
- Resposta da LLM com papel de analista financeiro sênior

## Sprint 3
- Persistência com SQLite via SQLAlchemy
- Chunking do texto em blocos de aproximadamente 2000 tokens
- Embeddings dos chunks com OpenAI
- Busca semântica com vetorizaÃ§Ã£o em Python puro para compatibilidade no Windows
- Fluxo RAG para responder perguntas com contexto recuperado

## Sprint 4
- Endpoint `POST /analyze` para extrair receita, EBITDA, lucro e dívida
- Cálculo de alavancagem, margem líquida e crescimento YoY
- Endpoint `POST /compare` para comparar dois relatórios
- Schemas Pydantic estruturados para respostas financeiras

## Interface visual
- `streamlit_app.py` fornece uma tela simples para upload do PDF e perguntas
- a interface conversa com a API em `http://localhost:8000`
- ideal para demonstração em portfólio sem depender de Swagger ou Postman

## Fluxo atual
1. `POST /upload` recebe o PDF.
2. O texto extraído fica salvo com um `document_id`.
3. `POST /ask` usa esse `document_id` para recuperar os chunks relevantes.
4. A pergunta e o contexto recuperado são enviados para a OpenAI, que devolve a resposta.
5. `POST /analyze` extrai os principais indicadores financeiros.
6. `POST /compare` compara dois relatórios lado a lado.

## Como rodar
1. Suba a API: `python -m uvicorn app.main:app --reload`
2. Em outro terminal, suba a interface: `streamlit run streamlit_app.py`

## Variáveis de ambiente
- `OPENAI_API_KEY=sua_chave`
- `OPENAI_CHAT_MODEL=gpt-5.4-mini`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- No arquivo `.env`, escreva sem aspas: `OPENAI_API_KEY=sk-...`
