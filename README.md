# Analisador de Relatórios Financeiros

API em FastAPI para receber PDFs financeiros, extrair texto e tabelas e, mais adiante, responder perguntas em linguagem natural.

## Sprint 1
- Upload de PDF
- Extração de texto com `pdfplumber`
- Validação de tipo e tamanho
- Testes com `pytest`

## Sprint 2
- Integração com a API da Anthropic
- Endpoint `POST /ask` com `document_id` e `question`
- Cache simples do texto do documento em memória
- Resposta da LLM com papel de analista financeiro sênior

## Fluxo atual
1. `POST /upload` recebe o PDF.
2. O texto extraído fica salvo em memória com um `document_id`.
3. `POST /ask` usa esse `document_id` para recuperar o texto.
4. A pergunta e o texto são enviados para a Anthropic, que devolve a resposta.
