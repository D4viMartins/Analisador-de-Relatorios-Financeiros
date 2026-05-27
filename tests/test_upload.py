import pytest
from fastapi.testclient import TestClient

from app.db.session import init_db
from app.main import app
from app.services.document_store import clear_database


@pytest.fixture()
def auth_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("APP_API_KEY", "test-api-key")
    init_db()
    clear_database()
    with TestClient(app, headers={"X-API-Key": "test-api-key"}) as test_client:
        yield test_client


def create_pdf_bytes(text: str = "Relatorio Financeiro Receita: 1000") -> bytes:
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream = f"BT /F1 18 Tf 72 720 Td ({safe_text}) Tj ET".encode("latin-1", errors="ignore")

    objects: list[bytes] = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>endobj\n",
        b"4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
        b"5 0 obj<< /Length " + str(len(content_stream)).encode("ascii") + b" >>stream\n" + content_stream + b"\nendstream endobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    xref = [b"xref\n", b"0 6\n", b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(b"".join(xref))
    pdf.extend(b"trailer<< /Size 6 /Root 1 0 R >>\n")
    pdf.extend(f"startxref\n{xref_start}\n%%EOF".encode("ascii"))
    return bytes(pdf)


def _fake_embeddings(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for index, _ in enumerate(texts):
        base = float(index + 1)
        vectors.append([base, 0.0, 0.0])
    return vectors


def _upload_document(client: TestClient, text: str, filename: str = "relatorio.pdf") -> dict[str, object]:
    response = client.post(
        "/upload",
        files={"file": (filename, create_pdf_bytes(text), "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()


def test_upload_pdf_success(auth_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.rag_service.embed_texts", _fake_embeddings)

    response = auth_client.post(
        "/upload",
        files={"file": ("relatorio.pdf", create_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"]
    assert payload["filename"] == "relatorio.pdf"
    assert "Receita" in payload["text"]
    assert payload["page_count"] == 1
    assert payload["table_count"] == 0


def test_upload_rejects_non_pdf(auth_client: TestClient) -> None:
    response = auth_client.post("/upload", files={"file": ("arquivo.txt", b"hello", "text/plain")})

    assert response.status_code == 400
    assert response.json()["detail"] == "Apenas arquivos PDF são aceitos."


def test_upload_rejects_oversized_file(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/upload",
        files={"file": ("relatorio.pdf", b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1), "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "O arquivo excede o limite de 10MB."


def test_ask_uses_retrieved_context(auth_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.rag_service.embed_texts", _fake_embeddings)
    monkeypatch.setattr("app.services.rag_service.generate_answer", lambda question, context: f"Resposta simulada para: {question}")

    upload_response = auth_client.post(
        "/upload",
        files={"file": ("relatorio.pdf", create_pdf_bytes(), "application/pdf")},
    )
    document_id = upload_response.json()["document_id"]

    response = auth_client.post("/ask", json={"document_id": document_id, "question": "Qual e a receita?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["question"] == "Qual e a receita?"
    assert payload["answer"] == "Resposta simulada para: Qual e a receita?"


def test_ask_rejects_unknown_document(auth_client: TestClient) -> None:
    response = auth_client.post("/ask", json={"document_id": "does-not-exist", "question": "Qual e a receita?"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Documento não encontrado."


def test_analyze_returns_structured_metrics(auth_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.rag_service.embed_texts", _fake_embeddings)

    upload_response = auth_client.post(
        "/upload",
        files={
            "file": (
                "relatorio.pdf",
                create_pdf_bytes(
                    "Receita liquida R$ 2.400.000 EBITDA ajustado R$ 500.000 Lucro liquido R$ 180.000 Divida bruta R$ 1.200.000 Crescimento de 12% em relacao ao ano anterior",
                ),
                "application/pdf",
            )
        },
    )
    document_id = upload_response.json()["document_id"]

    response = auth_client.post("/analyze", json={"document_id": document_id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["metrics"]["revenue"]["value"] == 2400000.0
    assert payload["metrics"]["ebitda"]["value"] == 500000.0
    assert payload["metrics"]["profit"]["value"] == 180000.0
    assert payload["metrics"]["debt"]["value"] == 1200000.0
    assert payload["indicators"]["net_margin"]["value"] == 7.5
    assert payload["indicators"]["leverage"]["value"] == 2.4


def test_compare_returns_deltas(auth_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.rag_service.embed_texts", _fake_embeddings)

    doc_a = auth_client.post(
        "/upload",
        files={
            "file": (
                "relatorio-1.pdf",
                create_pdf_bytes(
                    "Receita liquida R$ 2.000.000 EBITDA R$ 400.000 Lucro liquido R$ 100.000 Divida bruta R$ 900.000",
                ),
                "application/pdf",
            )
        },
    ).json()["document_id"]

    doc_b = auth_client.post(
        "/upload",
        files={
            "file": (
                "relatorio-2.pdf",
                create_pdf_bytes(
                    "Receita liquida R$ 2.500.000 EBITDA R$ 500.000 Lucro liquido R$ 150.000 Divida bruta R$ 800.000",
                ),
                "application/pdf",
            )
        },
    ).json()["document_id"]

    response = auth_client.post("/compare", json={"document_id_a": doc_a, "document_id_b": doc_b})

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_a"]["document_id"] == doc_a
    assert payload["document_b"]["document_id"] == doc_b
    assert payload["deltas"][0]["metric"] == "revenue"
    assert payload["deltas"][0]["document_a_value"] == 2000000.0
    assert payload["deltas"][0]["document_b_value"] == 2500000.0
    assert payload["deltas"][0]["absolute_change"] == 500000.0


def test_api_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_API_KEY", "test-api-key")
    init_db()
    clear_database()
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.post(
            "/upload",
            files={"file": ("relatorio.pdf", create_pdf_bytes(), "application/pdf")},
        )

    assert response.status_code == 401
