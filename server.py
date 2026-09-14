#!/usr/bin/env python3
import os
import re
import json
import csv
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote, urlparse

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTES_CSV = "notes.csv"
NOTES_FIELDS = [
    "ID",
    "IN_Notes",
    "IN_Flag_For_Review",
    "IN_Needs_Processing_QC",
    "IN_Cortical_Infarcts",
    "IN_Deep_Infarcts",
    "IN_Cerebellar_Infarcts",
    "IN_Infarct_Count",
]
VALID_INFARCT_PRESENCE = {"", "No", "Yes"}
VALID_INFARCT_COUNTS = {"0", "1", "2", "3", "4", "5", "6", "7", "8+"}

MODALITY_FIELDS = {
    "T1": "t1_path",
    "T2": "t2_path",
    "FLAIR": "flair_path",
}


def _natural_sort_key(value):
    parts = re.split(r"(\d+)", value.casefold())
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in parts), value


def list_subjects():
    if not os.path.isdir(DATA_DIR):
        return []

    subjects = []
    for entry in os.scandir(DATA_DIR):
        if not entry.is_dir(follow_symlinks=False):
            continue

        sid = entry.name
        subject = {"id": sid}
        has_modality = False
        for modality, field in MODALITY_FIELDS.items():
            filename = f"{sid}_{modality}.nii.gz"
            file_path = os.path.join(entry.path, filename)
            if os.path.isfile(file_path) and not os.path.islink(file_path):
                subject[field] = f"data/{quote(sid, safe='')}/{quote(filename, safe='')}"
                has_modality = True
            else:
                subject[field] = None

        if has_modality:
            subjects.append(subject)

    subjects.sort(key=lambda subject: _natural_sort_key(subject["id"]))
    return subjects


def _subject_sort_key(sid):
    return _natural_sort_key(sid)


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def _csv_bool(value):
    return "TRUE" if _parse_bool(value) else "FALSE"


def _normalize_review(value):
    if not isinstance(value, dict):
        value = {}
    cortical_infarcts = str(value.get("cortical_infarcts", value.get("IN_Cortical_Infarcts", "")) or "").strip()
    if cortical_infarcts not in VALID_INFARCT_PRESENCE:
        cortical_infarcts = ""

    deep_infarcts = str(value.get("deep_infarcts", value.get("IN_Deep_Infarcts", "")) or "").strip()
    if deep_infarcts not in VALID_INFARCT_PRESENCE:
        deep_infarcts = ""

    cerebellar_infarcts = str(value.get("cerebellar_infarcts", value.get("IN_Cerebellar_Infarcts", "")) or "").strip()
    if cerebellar_infarcts not in VALID_INFARCT_PRESENCE:
        cerebellar_infarcts = ""

    infarct_count = str(value.get("infarct_count", value.get("IN_Infarct_Count", "0")) or "0").strip()
    if infarct_count not in VALID_INFARCT_COUNTS:
        infarct_count = "0"

    return {
        "flag_for_review": _parse_bool(value.get("flag_for_review", value.get("IN_Flag_For_Review"))),
        "needs_processing_qc": _parse_bool(value.get("needs_processing_qc", value.get("IN_Needs_Processing_QC"))),
        "cortical_infarcts": cortical_infarcts,
        "deep_infarcts": deep_infarcts,
        "cerebellar_infarcts": cerebellar_infarcts,
        "infarct_count": infarct_count,
    }


def read_notes_csv():
    notes = {}
    review = {}
    if not os.path.isfile(NOTES_CSV):
        return notes, review
    try:
        with open(NOTES_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = (row.get("ID") or "").strip()
                txt = row.get("IN_Notes") or ""
                if sid:
                    notes[sid] = txt
                    review[sid] = _normalize_review(row)
    except Exception:
        return {}, {}
    return notes, review


def write_notes_csv(notes_map, review_map=None, subject_ids=None):
    review_map = review_map or {}
    rows = []
    if subject_ids:
        row_ids = subject_ids
    else:
        row_ids = sorted(set(notes_map.keys()) | set(review_map.keys()), key=_subject_sort_key)

    for sid in row_ids:
        review = _normalize_review(review_map.get(sid))
        rows.append({
            "ID": sid,
            "IN_Notes": notes_map.get(sid, ""),
            "IN_Flag_For_Review": _csv_bool(review["flag_for_review"]),
            "IN_Needs_Processing_QC": _csv_bool(review["needs_processing_qc"]),
            "IN_Cortical_Infarcts": review["cortical_infarcts"],
            "IN_Deep_Infarcts": review["deep_infarcts"],
            "IN_Cerebellar_Infarcts": review["cerebellar_infarcts"],
            "IN_Infarct_Count": review["infarct_count"],
        })

    with open(NOTES_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=NOTES_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return sum(
        1
        for r in rows
        if r["IN_Notes"]
        or r["IN_Flag_For_Review"] == "TRUE"
        or r["IN_Needs_Processing_QC"] == "TRUE"
        or r["IN_Cortical_Infarcts"]
        or r["IN_Deep_Infarcts"]
        or r["IN_Cerebellar_Infarcts"]
        or r["IN_Infarct_Count"] != "0"
    )


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _send_json(self, obj, status=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/subjects":
            subs = list_subjects()
            return self._send_json({"subjects": subs})

        if parsed.path == "/api/notes":
            notes, review = read_notes_csv()
            return self._send_json({"notes": notes, "review": review})

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/notes":
            self.send_error(404, "Not Found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            payload = json.loads(body) if body else {}

            notes_map = payload.get("notes", {})
            if not isinstance(notes_map, dict):
                return self._send_json({"ok": False, "error": "notes must be an object/dict"}, status=400)

            review_map = payload.get("review", {})
            if not isinstance(review_map, dict):
                return self._send_json({"ok": False, "error": "review must be an object/dict"}, status=400)

            subjects = list_subjects()
            subject_ids = [s["id"] for s in subjects]
            subject_id_set = set(subject_ids)

            cleaned = {}
            for k, v in notes_map.items():
                sid = str(k).strip()
                if sid not in subject_id_set:
                    continue
                cleaned[sid] = "" if v is None else str(v)

            cleaned_review = {}
            for k, v in review_map.items():
                sid = str(k).strip()
                if sid not in subject_id_set:
                    continue
                cleaned_review[sid] = _normalize_review(v)

            count = write_notes_csv(cleaned, cleaned_review, subject_ids=subject_ids)

            return self._send_json({"ok": True, "written": NOTES_CSV, "count": count})

        except Exception as e:
            return self._send_json({"ok": False, "error": str(e)}, status=500)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"FastReads VASC serving on http://127.0.0.1:{PORT}/viewer.html")
    httpd.serve_forever()
