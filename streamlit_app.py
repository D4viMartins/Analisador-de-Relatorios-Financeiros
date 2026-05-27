from __future__ import annotations

import httpx
import streamlit as st
from app.services.env_loader import load_dotenv_file

load_dotenv_file()

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Analisador de Relatórios Financeiros", layout="wide")

st.title("Analisador de Relatórios Financeiros")
st.caption("Envie um PDF, faça perguntas em linguagem natural e receba uma resposta na hora.")

col_upload, col_ask = st.columns(2)

with col_upload:
    st.subheader("1. Enviar PDF")
    uploaded_file = st.file_uploader("Escolha um PDF", type=["pdf"])

    if uploaded_file and st.button("Processar PDF", use_container_width=True):
        file_bytes = uploaded_file.getvalue()
        files = {"file": (uploaded_file.name, file_bytes, "application/pdf")}

        try:
            response = httpx.post(f"{API_BASE_URL}/upload", files=files, timeout=120)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", str(exc))
            st.error(f"Erro ao processar PDF: {detail}")
        except Exception as exc:
            st.error(f"Não foi possível conectar à API: {exc}")
        else:
            st.session_state["document_id"] = payload["document_id"]
            st.session_state["uploaded_filename"] = payload["filename"]
            st.success("PDF processado com sucesso.")
            st.write("**Arquivo:**", payload["filename"])

with col_ask:
    st.subheader("2. Fazer pergunta")
    question = st.text_area("Pergunta", placeholder="Ex.: Qual foi a receita líquida?")

    if st.button("Perguntar", use_container_width=True):
        document_id = st.session_state.get("document_id")
        if not document_id:
            st.warning("Envie um PDF primeiro.")
        elif not question.strip():
            st.warning("Digite uma pergunta antes de enviar.")
        else:
            try:
                response = httpx.post(
                    f"{API_BASE_URL}/ask",
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
                st.text(payload["answer"])
