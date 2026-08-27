from __future__ import annotations
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import zipfile
import re

from docx import Document
from pypdf import PdfReader


@dataclass
class ManuscriptBundle:
    filename: str
    text: str
    tables: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    source_bytes: bytes | None = None


def _docx_text_and_tables(data: bytes) -> tuple[str, list[dict]]:
    doc = Document(BytesIO(data))
    chunks: list[str] = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            chunks.append(t)
    tables: list[dict] = []
    for i, table in enumerate(doc.tables, 1):
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if rows:
            tables.append({"index": i, "rows": rows})
            chunks.append(f"\n[TABLE {i}]\n" + "\n".join(" | ".join(r) for r in rows))
    return "\n".join(chunks), tables


def _docx_images(data: bytes) -> list[dict]:
    """Extract embedded images in document display order when possible."""
    import xml.etree.ElementTree as ET
    images: list[dict] = []
    with zipfile.ZipFile(BytesIO(data)) as zf:
        try:
            rels_root = ET.fromstring(zf.read("word/_rels/document.xml.rels"))
            rels = {}
            for rel in rels_root:
                rid = rel.attrib.get("Id")
                target = rel.attrib.get("Target", "")
                if rid and "media/" in target:
                    rels[rid] = "word/" + target.lstrip("/")
            doc_root = ET.fromstring(zf.read("word/document.xml"))
            ns = {
                "a":"http://schemas.openxmlformats.org/drawingml/2006/main",
                "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            }
            seen = set()
            for blip in doc_root.findall(".//a:blip", ns):
                rid = blip.attrib.get("{%s}embed" % ns["r"])
                name = rels.get(rid)
                if not name or name in seen or name not in zf.namelist():
                    continue
                seen.add(name)
                blob = zf.read(name)
                ext = Path(name).suffix.lower().lstrip(".") or "png"
                images.append({"name": Path(name).name, "ext": ext, "bytes": blob})
            if images:
                return images
        except Exception:
            pass
        for name in sorted(zf.namelist()):
            if name.startswith("word/media/"):
                blob = zf.read(name)
                ext = Path(name).suffix.lower().lstrip(".") or "png"
                images.append({"name": Path(name).name, "ext": ext, "bytes": blob})
    return images


def parse_upload(uploaded) -> ManuscriptBundle:
    data = uploaded.getvalue()
    name = uploaded.name
    suffix = Path(name).suffix.lower()
    if suffix == ".docx":
        text, tables = _docx_text_and_tables(data)
        return ManuscriptBundle(name, text, tables, _docx_images(data), data)
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return ManuscriptBundle(name, text, [], [], data)
    if suffix in {".txt", ".md"}:
        return ManuscriptBundle(name, data.decode("utf-8", errors="replace"), [], [], data)
    raise ValueError("Supported manuscript formats: DOCX, PDF, TXT, Markdown.")


def count_citations(text: str) -> int:
    return len(re.findall(r"\[(?:\d+(?:\s*[-–,]\s*\d+)*)\]", text))
