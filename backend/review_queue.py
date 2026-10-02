"""Persistent human-review queue for low-trust AI reports with transactional inter-process locking."""
from __future__ import annotations
import uuid
import json
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import fcntl
except ImportError:
    fcntl = None


@contextmanager
def file_lock(path: Path):
    if fcntl is None:
        yield
        return
    lock_path = path.with_suffix(".lock")
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
        except Exception:
            pass


class ReviewQueue:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write(self, data: list[dict[str, Any]]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def enqueue(self, report_id: str, reasons: list[str], priority: str, summary: dict[str, Any]) -> dict[str, Any]:
        with self.lock, file_lock(self.path):
            rows = self._read()
            existing = next((r for r in rows if r.get("report_id") == report_id and r.get("status") == "pending"), None)
            if existing:
                return existing
            item = {
                "review_id": f"REV-{uuid.uuid4().hex[:12].upper()}",
                "report_id": report_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending",
                "priority": priority,
                "reasons": reasons,
                "summary": summary,
                "reviewer": None,
                "review_notes": None,
                "decision": None,
                "updated_at": None,
            }
            rows.append(item)
            self._write(rows)
            return item

    def list(self, status: Optional[str] = None) -> list[dict[str, Any]]:
        with self.lock, file_lock(self.path):
            rows = self._read()
            if status:
                rows = [r for r in rows if r.get("status") == status]
            return rows

    def get(self, review_id: str) -> Optional[dict[str, Any]]:
        with self.lock, file_lock(self.path):
            return next((r for r in self._read() if r.get("review_id") == review_id), None)

    def resolve(self, review_id: str, reviewer: str, decision: str, notes: str = "") -> dict[str, Any]:
        if decision not in {"confirmed", "rejected", "needs_more_evidence"}:
            raise ValueError("decision must be confirmed, rejected, or needs_more_evidence")
        with self.lock, file_lock(self.path):
            rows = self._read()
            for item in rows:
                if item.get("review_id") == review_id:
                    item["status"] = "resolved"
                    item["reviewer"] = reviewer
                    item["decision"] = decision
                    item["review_notes"] = notes
                    item["updated_at"] = datetime.now(timezone.utc).isoformat()
                    self._write(rows)
                    return item
        raise KeyError(review_id)
