#!/usr/bin/env python3
"""Discover public faculty timetable PDFs and extract reviewable space labels.

Requires Poppler (pdftotext/pdftoppm); Tesseract ara+eng is used for image pages.
No student identifiers, names, or timetable cell contents are emitted to the registry.
This discovers labels, not architectural topology or authoritative room availability.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "teaching": "https://ci.tanta.edu.eg/stu_study_tables.aspx",
    "examinations": "https://ci.tanta.edu.eg/stu-exam-tables.aspx",
}
NS = "{http://www.w3.org/1999/xhtml}"
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
VOCAB = ("معمل", "مدرج", "قاعة", "المكان", "المركزي", "العلوي", "السفلي", "أونلاين", "أونالين")


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(ARABIC_DIGITS)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return re.sub(r"\s+", " ", text).strip()


def logical_text(text: str) -> str:
    """Poppler sometimes returns Arabic in visual order. Keep digit/Latin runs intact."""
    direct = normalized(text)
    reverse = re.sub(r"[A-Za-z0-9]+", lambda m: m[0][::-1], direct[::-1])
    score = lambda x: sum(x.count(w) for w in VOCAB)
    return reverse if score(reverse) > score(direct) else direct


def safe_url(url: str) -> str:
    return quote(unquote(url), safe=":/?=&%")


def fetch(url: str) -> bytes:
    req = Request(safe_url(url), headers={"User-Agent": "Tanta-FCI-project-research/0.1"})
    with urlopen(req, timeout=40) as response:
        return response.read(30 * 1024 * 1024 + 1)


class PdfLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        href = attrs.get("href", "")
        if tag == "a" and urlsplit(href).path.lower().endswith(".pdf"):
            self.links.append(href)


def discover() -> list[dict]:
    found: dict[str, dict] = {}
    for category, page in PAGES.items():
        parser = PdfLinks()
        parser.feed(fetch(page).decode("utf-8-sig", "replace"))
        for href in parser.links:
            url = safe_url(urljoin(page, href))
            path = unquote(urlsplit(url).path).lower()
            if urlsplit(url).hostname != "ci.tanta.edu.eg":
                continue
            # Exclude student guides, registration instructions and unrelated policy PDFs.
            if not any(part in path for part in ("stu_tables/", "stu_exams/", "exam-table")):
                continue
            source_id = hashlib.sha256(url.encode()).hexdigest()[:16]
            found[url] = {"source_id": source_id, "url": url,
                          "category": category, "index_page": page,
                          "filename": unquote(urlsplit(url).path.rsplit("/", 1)[-1])}
    return sorted(found.values(), key=lambda d: d["url"])


def download(document: dict, cache: Path, reuse_cache: bool = False) -> dict:
    result = dict(document)
    try:
        old_path = (ROOT / document["cache_file"]).resolve() if document.get("cache_file") else None
        if old_path and not old_path.is_relative_to(cache.resolve()):
            raise ValueError("Cache path is outside the PDF cache")
        data = old_path.read_bytes() if reuse_cache and old_path and old_path.exists() else fetch(document["url"])
        if len(data) > 30 * 1024 * 1024 or not data.startswith(b"%PDF-"):
            raise ValueError("Response is not a supported PDF (or exceeds 30 MiB)")
        digest = hashlib.sha256(data).hexdigest()
        path = cache / (document["source_id"] + "-" + digest + ".pdf")
        if not path.exists():
            path.write_bytes(data)
        result.update(status="downloaded", bytes=len(data),
                      sha256=digest,
                      cache_file=str(path.relative_to(ROOT)))
    except Exception as exc:
        result.update(status="download_failed", error=type(exc).__name__)
    return result


def space_label(text: str, in_location_column: bool) -> tuple[str, str, str] | None:
    """Return provisional key, normalized display label, proposed kind."""
    text = logical_text(text).strip(" .,:;،()[]-–—")
    text = re.sub(r"[أإآ]", "ا", text)
    if re.fullmatch(r"(?:اونلاين|اونالين|اون لاين|online|on line|عن بعد)", text, re.I):
        return "virtual-online", "Online / أونلاين", "virtual"
    patterns = [
        (r"(?:معمل|lab(?:oratory)?)\s*([A-H]|\d{1,2})", "lab", "laboratory", "معمل"),
        (r"(?:مدرج|lecture hall)\s*(\d{1,2})", "hall", "lecture_hall", "مدرج"),
        (r"(?:قاعة|classroom)\s*(\d{1,2})", "classroom", "classroom", "قاعة"),
    ]
    for pattern, prefix, kind, arabic in patterns:
        match = re.fullmatch(pattern, text, re.I)
        if match:
            code = match[1].upper()
            return f"{prefix}-{code}", f"{arabic} {code}", kind
    if in_location_column:
        match = re.fullmatch(r"([B-H])", text)
        if match:
            return f"letter-{match[1]}", match[1], "unconfirmed"
        if re.fullmatch(r"(?:المدرج\s*)?المركزي(?:\s+(?:العلوي|السفلي|الارضي))?", text):
            suffix = text.replace("المدرج", "").strip()
            return "central-" + suffix.replace(" ", "-"), suffix, "lecture_hall"
    return None


def text_pages(path: Path) -> list[dict]:
    result = subprocess.run(["pdftotext", "-bbox-layout", str(path), "-"],
                            capture_output=True, check=True, timeout=50)
    root = ET.fromstring(result.stdout)
    pages = []
    for page in root.iter(NS + "page"):
        lines = []
        for line in page.iter(NS + "line"):
            words = [{"text": logical_text("".join(w.itertext())),
                      "x0": float(w.get("xMin")), "x1": float(w.get("xMax"))}
                     for w in line if w.tag == NS + "word"]
            lines.append({"text": logical_text(" ".join("".join(w.itertext()) for w in line)),
                          "x0": float(line.get("xMin")), "x1": float(line.get("xMax")),
                          "y0": float(line.get("yMin")), "y1": float(line.get("yMax")),
                          "words": words, "method": "embedded_text"})
        pages.append({"width": float(page.get("width")),
                      "height": float(page.get("height")), "lines": lines})
    return pages


def ocr_page(path: Path, number: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="tanta-pdf-ocr-") as folder:
        base = Path(folder) / "page"
        subprocess.run(["pdftoppm", "-f", str(number), "-l", str(number), "-r", "180",
                        "-png", "-singlefile", str(path), str(base)],
                       check=True, capture_output=True, timeout=60)
        output = subprocess.run(["tesseract", str(base) + ".png", "stdout", "-l", "ara+eng",
                                 "--psm", "11", "tsv"], check=True, capture_output=True,
                                timeout=90).stdout.decode("utf-8", "replace")
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(output), delimiter="\t"))
    image_page = next(r for r in rows if r["level"] == "1")
    grouped: dict[tuple, list] = defaultdict(list)
    for row in rows:
        if row["level"] == "5" and row.get("text", "").strip():
            grouped[(row["block_num"], row["par_num"], row["line_num"])].append(row)
    lines = []
    for words in grouped.values():
        x0 = min(int(w["left"]) for w in words)
        y0 = min(int(w["top"]) for w in words)
        x1 = max(int(w["left"]) + int(w["width"]) for w in words)
        y1 = max(int(w["top"]) + int(w["height"]) for w in words)
        # Tesseract TSV words are in reading order; do not reverse normal Arabic.
        text = logical_text(" ".join(w["text"] for w in words))
        lines.append({"text": text, "x0": x0, "x1": x1, "y0": y0, "y1": y1,
                      "method": "ocr", "words": [
                          {"text": logical_text(w["text"]), "x0": int(w["left"]),
                           "x1": int(w["left"]) + int(w["width"])} for w in words]})
    return {"width": int(image_page["width"]), "height": int(image_page["height"]),
            "lines": lines}


def observations(document: dict, use_ocr: bool) -> tuple[list[dict], dict]:
    if document["status"] != "downloaded":
        return [], {}
    path = ROOT / document["cache_file"]
    pages = text_pages(path)
    found = []
    stats = Counter(pages=len(pages))
    for number, page in enumerate(pages, 1):
        if sum(len(re.findall(r"[\u0600-\u06ffA-Za-z]", x["text"])) for x in page["lines"]) < 35:
            if use_ocr:
                page = ocr_page(path, number)
                stats["ocr_pages"] += 1
            else:
                stats["image_pages_not_scanned"] += 1
        headers = [w for line in page["lines"] for w in line["words"]
                   if w["text"].strip(":/ ") in {"المكان", "القاعة"}]
        centers = [(h["x0"] + h["x1"]) / 2 for h in headers]
        if not centers:
            stats["pages_without_location_header"] += 1
        for line in page["lines"]:
            center = (line["x0"] + line["x1"]) / 2
            in_column = any(abs(center - c) < page["width"] * .055 for c in centers)
            if line["x1"] - line["x0"] > page["width"] * .24:
                continue
            label = space_label(line["text"], in_column)
            if label is None:
                continue
            key, display, kind = label
            found.append({"candidate_key": key, "observed_label": display,
                          "proposed_kind": kind, "source_id": document["source_id"],
                          "page": number, "method": line["method"],
                          "location_column_confirmed": in_column,
                          "bbox_fraction": [round(line["x0"] / page["width"], 5),
                                            round(line["y0"] / page["height"], 5),
                                            round(line["x1"] / page["width"], 5),
                                            round(line["y1"] / page["height"], 5)]})
    stats["location_observations"] = len(found)
    return found, dict(stats)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-ocr", action="store_true", help="Explicitly report image pages as unscanned")
    parser.add_argument("--rescan-cache", action="store_true", help="Reuse the saved source index")
    args = parser.parse_args()
    out = ROOT / "data/public"
    cache = out / "pdf-cache"
    cache.mkdir(parents=True, exist_ok=True)
    sources_file = out / "source_documents.json"
    docs = json.loads(sources_file.read_text())["documents"] if args.rescan_cache else discover()
    with ThreadPoolExecutor(max_workers=4) as pool:
        downloaded = list(pool.map(lambda d: download(d, cache, args.rescan_cache), docs))
    all_observations = []
    for index, doc in enumerate(downloaded, 1):
        try:
            found, stats = observations(doc, not args.no_ocr)
            all_observations.extend(found)
            doc["scan"] = stats
        except Exception as exc:
            doc["scan_error"] = type(exc).__name__
        print(f"[{index}/{len(downloaded)}] {doc['source_id']} {doc['status']} "
              f"observations={doc.get('scan', {}).get('location_observations', 0)}", flush=True)
    stamp = datetime.now(timezone.utc).isoformat()
    sources_file.write_text(json.dumps({"retrieved_at": stamp, "documents": downloaded},
                                       ensure_ascii=False, indent=2) + "\n")
    grouped = defaultdict(list)
    for row in all_observations:
        grouped[row["candidate_key"]].append(row)
    candidates = []
    for key, rows in sorted(grouped.items()):
        candidates.append({"candidate_key": key, "university_key": "tanta-university",
                           "faculty_key": "computers-and-informatics",
                           "display_label": rows[0]["observed_label"],
                           "proposed_kind": rows[0]["proposed_kind"],
                           "status": "pending_review", "approved_for_scheduling": False,
                           "campus_id": None, "building_id": None, "floor_id": None,
                           "seated_capacity": None, "exam_capacity": None,
                           "usable_workstations": None, "opening_hours": None,
                           "physical_identity_confirmed": False,
                           "document_count": len({r['source_id'] for r in rows}),
                           "observation_count": len(rows), "evidence": rows})
    (out / "space_candidates.json").write_text(json.dumps({
        "generated_at": stamp,
        "scope": "Observed labels in linked public teaching/examination PDFs, not a complete architecture survey",
        "identity_warning": "The same label can identify different spaces in different buildings. No physical identity merge is approved.",
        "candidates": candidates}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"documents": len(downloaded), "downloaded": sum(d["status"] == "downloaded" for d in downloaded),
                      "scan_errors": sum("scan_error" in d for d in downloaded),
                      "candidates": len(candidates), "observations": len(all_observations)}, indent=2))


if __name__ == "__main__":
    main()
