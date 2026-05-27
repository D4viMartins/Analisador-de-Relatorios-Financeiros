from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_store import clear_documents

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_document_store() -> None:
    clear_documents()


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


def test_upload_pdf_success() -> None:
    pdf_bytes = create_pdf_bytes()
    files = {"file": ("relatorio.pdf", pdf_bytes, "application/pdf")}

    response = client.post("/upload", files=files)

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"]
    assert payload["filename"] == "relatorio.pdf"
    assert "Receita" in payload["text"]
    assert payload["page_count"] == 1
    assert payload["table_count"] == 0


def test_upload_rejects_non_pdf() -> None:
    files = {"file": ("arquivo.txt", b"hello", "text/plain")}

    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert response.json()["detail"] == "Apenas arquivos PDF são aceitos."


def test_upload_rejects_oversized_file() -> None:
    files = {"file": ("relatorio.pdf", b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1), "application/pdf")}

    response = client.post("/upload", files=files)

    assert response.status_code == 413
    assert response.json()["detail"] == "O arquivo excede o limite de 10MB."


@dataclass
class _FakeTextBlock:
    text: str


@dataclass
class _FakeAnthropicResponse:
    content: list[_FakeTextBlock]


class _FakeMessages:
    def create(self, **kwargs):
        assert kwargs["model"] == "claude-sonnet-4-20250514"
        return _FakeAnthropicResponse(content=[_FakeTextBlock(text="A receita está em 1000.")])


class _FakeAnthropicClient:
    messages = _FakeMessages()


def test_ask_uses_cached_document_text(monkeypatch) -> None:
    upload_response = client.post("/upload", files={"file": ("relatorio.pdf", create_pdf_bytes(), "application/pdf")})
    document_id = upload_response.json()["document_id"]

    monkeypatch.setattr("app.services.anthropic_service.get_anthropic_client", lambda: _FakeAnthropicClient())

    response = client.post("/ask", json={"document_id": document_id, "question": "Qual é a receita?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["question"] == "Qual é a receita?"
    assert payload["answer"] == "A receita está em 1000."


def test_ask_rejects_unknown_document() -> None:
    response = client.post("/ask", json={"document_id": "does-not-exist", "question": "Qual é a receita?"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Documento não encontrado."
