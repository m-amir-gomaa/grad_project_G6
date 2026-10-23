"""Persist PDF observations in a university-scoped local reference database."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    existing = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='universities'").fetchone()
    if existing and db.execute("PRAGMA user_version").fetchone()[0] != 1:
        db.close()
        raise ValueError("Existing database requires an explicit schema migration; it was not modified")
    db.executescript((Path(__file__).parent / "schema.sql").read_text())
    db.execute("PRAGMA user_version=1")
    return db


def spaces_at(db: sqlite3.Connection, university_id: str, instant_utc: str) -> list[tuple]:
    """Latest approved version per space at a canonical UTC ISO timestamp."""
    return db.execute("""SELECT sv.id,sv.space_id,sv.name,sv.state,sv.reviewed_for_scheduling
        FROM space_versions sv JOIN architecture_revisions ar
          ON ar.university_id=sv.university_id AND ar.id=sv.architecture_revision_id
        WHERE sv.university_id=? AND ar.status='approved' AND ar.effective_from<=?
          AND NOT EXISTS (
            SELECT 1 FROM space_versions newer JOIN architecture_revisions nr
              ON nr.university_id=newer.university_id AND nr.id=newer.architecture_revision_id
            WHERE newer.university_id=sv.university_id AND newer.space_id=sv.space_id
              AND nr.status='approved' AND nr.effective_from<=? AND nr.effective_from>ar.effective_from)
        ORDER BY sv.space_id""", (university_id, instant_utc, instant_utc)).fetchall()


def import_candidates(db: sqlite3.Connection, university_id: str,
                      documents: list[dict], candidates: list[dict]) -> None:
    """Idempotent observation import. It never approves spaces or invents a layout."""
    if not db.execute("SELECT 1 FROM universities WHERE id=?", (university_id,)).fetchone():
        raise ValueError("Unknown university profile")
    if any(row.get("university_key", university_id) != university_id for row in candidates):
        raise ValueError("Imported candidates belong to another university")
    with db:
        # Content-addressed source versions preserve evidence when a URL's PDF changes.
        source_versions = {}
        for doc in documents:
            version_id = doc["source_id"] + ":" + (doc.get("sha256") or "download-failed")
            source_versions[doc["source_id"]] = version_id
            db.execute("""INSERT INTO source_documents VALUES (?,?,?,?,?,?)
                ON CONFLICT(university_id,id) DO NOTHING""",
                       (university_id, version_id, doc["source_id"], doc["url"], doc.get("sha256"),
                        json.dumps(doc.get("scan", {}))))
        for candidate in candidates:
            db.execute("""INSERT INTO import_candidates VALUES (?,?,?,?,?,NULL)
                ON CONFLICT(university_id,id) DO NOTHING""",
                       (university_id, candidate["candidate_key"], candidate["display_label"],
                        candidate["proposed_kind"], "pending_review"))
            for row in candidate["evidence"]:
                source_id = source_versions[row["source_id"]]
                key = json.dumps([candidate["candidate_key"], source_id, row["page"], row["bbox_fraction"]])
                observation_id = hashlib.sha256(key.encode()).hexdigest()
                db.execute("INSERT OR IGNORE INTO import_observations VALUES (?,?,?,?,?,?,?)",
                           (university_id, observation_id, candidate["candidate_key"], source_id,
                            row["page"], row["method"], json.dumps(row["bbox_fraction"])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="data/public/tanta-registry.sqlite")
    args = parser.parse_args()
    db = connect(args.database)
    with db:
        db.execute("INSERT OR IGNORE INTO universities VALUES (?,?,?,?)",
                   ("tanta-university", "Tanta University", "Africa/Cairo", "draft"))
    public = ROOT / "data/public"
    documents = json.loads((public / "source_documents.json").read_text())["documents"]
    candidates = json.loads((public / "space_candidates.json").read_text())["candidates"]
    import_candidates(db, "tanta-university", documents, candidates)
    print(json.dumps({"database": args.database, "university_id": "tanta-university",
                      "source_documents": len(documents), "pending_candidates": len(candidates),
                      "approved_spaces": db.execute("SELECT COUNT(*) FROM spaces WHERE university_id=?",
                                                    ("tanta-university",)).fetchone()[0]}, indent=2))
    db.close()


if __name__ == "__main__":
    main()
