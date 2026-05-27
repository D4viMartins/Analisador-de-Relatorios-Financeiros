# Analisador de Relatórios Financeiros

API em FastAPI para receber PDFs financeiros, extrair texto e tabelas e, mais adiante, responder perguntas em linguagem natural.

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
- Busca semântica com FAISS
- Fluxo RAG para responder perguntas com contexto recuperado

## Fluxo atual
1. `POST /upload` recebe o PDF.
2. O texto extraído fica salvo em memória com um `document_id`.
3. `POST /ask` usa esse `document_id` para recuperar os chunks relevantes.
4. A pergunta e o contexto recuperado são enviados para a OpenAI, que devolve a resposta.
