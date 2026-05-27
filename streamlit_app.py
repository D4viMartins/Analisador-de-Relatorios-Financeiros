from __future__ import annotations

import httpx
import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Analisador de Relatórios Financeiros", layout="wide")

st.title("Analisador de Relatórios Financeiros")
st.caption("Envie um PDF, receba um document_id e faça perguntas em linguagem natural.")

with st.sidebar:
    st.header("Configuração")
    api_base_url = st.text_input("API base URL", value=API_BASE_URL)
    st.write("Backend esperado em `http://localhost:8000`.")

col_upload, col_ask = st.columns(2)

with col_upload:
    st.subheader("1. Enviar PDF")
    uploaded_file = st.file_uploader("Escolha um PDF", type=["pdf"])

    if uploaded_file and st.button("Processar PDF", use_container_width=True):
        file_bytes = uploaded_file.getvalue()
        files = {"file": (uploaded_file.name, file_bytes, "application/pdf")}

        try:
            response = httpx.post(f"{api_base_url}/upload", files=files, timeout=120)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            st.error(f"Erro ao processar PDF: {exc.response.json().get('detail', str(exc))}")
        except Exception as exc:
            st.error(f"Não foi possível conectar à API: {exc}")
        else:
            st.session_state["document_id"] = payload["document_id"]
            st.session_state["uploaded_filename"] = payload["filename"]
            st.session_state["uploaded_text"] = payload["text"]
            st.success("PDF processado com sucesso.")
            st.write("**document_id:**", payload["document_id"])
            st.write("**Arquivo:**", payload["filename"])
            st.text_area("Texto extraído", value=payload["text"], height=240)

with col_ask:
    st.subheader("2. Fazer pergunta")
    document_id = st.text_input("document_id", value=st.session_state.get("document_id", ""))
    question = st.text_area("Pergunta", placeholder="Ex.: Qual foi a receita líquida?")

    if st.button("Perguntar", use_container_width=True):
        if not document_id:
            st.warning("Envie um PDF primeiro ou informe um document_id válido.")
        elif not question.strip():
            st.warning("Digite uma pergunta antes de enviar.")
        else:
            try:
                response = httpx.post(
                    f"{api_base_url}/ask",
                    json={"document_id": document_id, "question": question},
                    timeout=120,
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.json().get("detail", str(exc))
                st.error(f"Erro na pergunta: {detail}")
            except Exception as exc:
                st.error(f"Não foi possível conectar à API: {exc}")
            else:
                st.success("Resposta recebida.")
                st.write("**Resposta:**")
                st.write(payload["answer"])

st.divider()
st.subheader("Fluxo da demo")
st.markdown(
    """
1. Você envia um PDF.
2. A API extrai o texto e salva no SQLite.
3. A página mostra o `document_id`.
4. Você pergunta algo usando esse `document_id`.
5. A API recupera os chunks relevantes com FAISS.
6. A OpenAI responde com base no contexto recuperado.
"""
)
