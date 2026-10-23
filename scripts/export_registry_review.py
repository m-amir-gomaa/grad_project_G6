#!/usr/bin/env python3
"""Export the saved PDF scan as an Arabic-friendly CSV and a review report."""
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public"
documents = json.loads((PUBLIC / "source_documents.json").read_text())
registry = json.loads((PUBLIC / "space_candidates.json").read_text())
sources = {d["source_id"]: d for d in documents["documents"]}
rows = registry["candidates"]
keys = {r["candidate_key"] for r in rows}

with (PUBLIC / "space_registry.csv").open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.writer(file)
    writer.writerow(["university_id", "candidate_key", "observed_label", "proposed_kind",
                     "possible_alias_requires_review", "document_count", "observation_count",
                     "building_id", "floor_id", "seated_capacity", "exam_capacity",
                     "usable_workstations", "approved_for_scheduling", "source_url", "source_page"])
    for row in rows:
        alias = "lab-" + row["candidate_key"][-1] if row["candidate_key"].startswith("letter-") else ""
        evidence = row["evidence"][0]
        writer.writerow(["tanta-university", row["candidate_key"], row["display_label"], row["proposed_kind"],
                         alias if alias in keys else "", row["document_count"], row["observation_count"],
                         "", "", "", "", "", "false", sources[evidence["source_id"]]["url"], evidence["page"]])

summary = {
    "generated_at": registry["generated_at"],
    "scanner_code_sha256_at_export": hashlib.sha256((ROOT / "scripts/scan_faculty_pdfs.py").read_bytes()).hexdigest(),
    "pdf_documents": len(sources),
    "distinct_pdf_content_hashes": len({d.get("sha256") for d in sources.values()}),
    "pages": sum(d.get("scan", {}).get("pages", 0) for d in sources.values()),
    "ocr_pages": sum(d.get("scan", {}).get("ocr_pages", 0) for d in sources.values()),
    "scan_errors": sum("scan_error" in d for d in sources.values()),
    "download_failures": sum(d["status"] != "downloaded" for d in sources.values()),
    "unscanned_image_pages": sum(d.get("scan", {}).get("image_pages_not_scanned", 0) for d in sources.values()),
    "pages_without_detected_location_header": sum(d.get("scan", {}).get("pages_without_location_header", 0) for d in sources.values()),
    "provisional_labels": len(rows),
    "physical_location_labels": sum(r["proposed_kind"] != "virtual" for r in rows),
    "observations": sum(r["observation_count"] for r in rows),
    "observation_methods": dict(Counter(e["method"] for r in rows for e in r["evidence"])),
    "not_a_complete_room_count": True,
    "approved_for_scheduling": 0,
}
(PUBLIC / "scan_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
report = ["# Provisional Tanta FCI space registry from published timetables", "",
          "Generated from the linked public teaching and examination PDFs; scan timestamp: " + registry["generated_at"] + ".", "",
          f"Scanned **{summary['pdf_documents']} distinct PDFs**, **{summary['pages']} pages**, including "
          f"**{summary['ocr_pages']} pages using Arabic/English OCR**. Found **{summary['observations']} label observations** "
          f"and **{len(rows)} provisional label groups**: {summary['physical_location_labels']} physical location labels plus an online marker.", "",
          "An observation is a label appearance, not a room, activity, or capacity. Repeated labels and possible aliases remain unresolved. "
          "All extracted candidates are pending review; buildings, floors, geometry, capacities, and opening hours remain unset.", "",
          "| Candidate | Observed label | Proposed type | PDFs | Appearances | Example evidence |",
          "|---|---|---|---:|---:|---|"]
for row in rows:
    evidence = row["evidence"][0]
    url = sources[evidence["source_id"]]["url"] + "#page=" + str(evidence["page"])
    report.append(f"| `{row['candidate_key']}` | {row['display_label']} | {row['proposed_kind']} | "
                  f"{row['document_count']} | {row['observation_count']} | [PDF p. {evidence['page']}]({url}) |")
report += ["", "## Interpretation and review", "",
           "- `letter-C` and `lab-C` might refer to the same space; they have not been merged. The same applies to D–H.",
           "- Numbered laboratories and numbered lecture halls are separate candidates even when their numbers match.",
           "- The two central-hall labels do not establish their building or architectural floor. Their wording is preserved as a label.",
           "- Online is a delivery marker and must not become a physical room.",
           "- A lab B appears in the separately reviewed student-guide inventory, but was not found as a location label in this timetable scan. It is not silently added as a timetable finding.",
           "- Some exam PDFs contain courses/dates without room information. OCR does not recover information that is absent from a document.",
           "- Location extraction uses exact short labels and spatial evidence where a location-column header was found. Unqualified matches remain visible in the detailed evidence and require review.",
           "- No blank timetable cell is treated as free capacity, and no complete student enrolment list is inferred from these PDFs.",
           "- Building/floor mapping, physical identity, operational capacity, shared ownership and current availability need faculty data.", "",
           "## Files", "",
           "- [Reviewable CSV](../data/public/space_registry.csv)",
           "- [Detailed observations with source/page/bounding box](../data/public/space_candidates.json)",
           "- [Source URLs and SHA-256 checksums](../data/public/source_documents.json)",
           "- [Machine-readable scan totals](../data/public/scan_summary.json)", "",
           "The local SQLite profile stores these as import candidates under `tanta-university`, not approved scheduling spaces. "
           "PDF caching and source extraction are reproducible with `scripts/scan_faculty_pdfs.py`."]
(ROOT / "research/PDF-SPACE-REGISTRY.md").write_text("\n".join(report) + "\n")
print(json.dumps(summary, indent=2))
