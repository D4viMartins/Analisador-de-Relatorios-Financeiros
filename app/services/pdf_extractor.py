from __future__ import annotations

from io import BytesIO
from typing import Any

import pdfplumber


def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    text_parts: list[str] = []
    tables: list[list[list[str | None]]] = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text.strip())

            page_tables = page.extract_tables() or []
            for table in page_tables:
                normalized_table: list[list[str | None]] = []
                for row in table:
                    normalized_row = [cell if cell is None else str(cell) for cell in row]
                    normalized_table.append(normalized_row)
                tables.append(normalized_table)

        page_count = len(pdf.pages)

    combined_text = "\n\n".join(text_parts).strip()

    return {
        "text": combined_text,
        "tables": tables,
        "page_count": page_count,
        "table_count": len(tables),
    }
