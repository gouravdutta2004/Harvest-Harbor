import hashlib
import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import fcntl
except ImportError:
    fcntl = None


@contextmanager
def file_lock(path: str):
    if fcntl is None:
        yield
        return
    lock_path = path + ".lock"
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            except Exception:
                pass
    finally:
        try:
            lock_file.close()
        except Exception:
            pass


class EvidenceBlockchain:
    def __init__(self, storage_path: str):
        self.storage_path = os.path.abspath(storage_path)
        self._lock = threading.Lock()
        self.chain: List[Dict[str, Any]] = []
        self._load_chain()

    @staticmethod
    def calculate_hash(block: Dict[str, Any]) -> str:
        data = dict(block)
        data.pop("current_hash", None)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _genesis(self) -> Dict[str, Any]:
        b = {
            "block_index": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_id": "GENESIS",
            "block_type": "genesis",
            "data": {"message": "Crop Disease AI Evidence Chain Genesis Block"},
            "previous_hash": "0",
        }
        b["current_hash"] = self.calculate_hash(b)
        return b

    def _load_chain(self):
        if not os.path.exists(self.storage_path):
            self.chain = [self._genesis()]
            self._save_chain()
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.chain = json.load(f)
            if not isinstance(self.chain, list):
                raise ValueError("Evidence chain must be a JSON list.")
            if not self.chain:
                self.chain = [self._genesis()]
                self._save_chain()
        except Exception as e:
            raise RuntimeError(f"Failed to load evidence chain: {e}") from e

    def _save_chain(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.chain, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.storage_path)

    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        return self.chain[-1] if self.chain else None

    def add_block(self, report_id: str, evidence_data: Dict[str, Any], block_type: str = "evidence") -> Dict[str, Any]:
        if not report_id:
            raise ValueError("report_id is required.")
        if not isinstance(evidence_data, dict):
            raise ValueError("evidence_data must be a dictionary.")
        with self._lock, file_lock(self.storage_path):
            self._load_chain()
            last = self.get_latest_block()
            if last is None:
                raise RuntimeError("Evidence chain is empty.")
            b = {
                "block_index": int(last["block_index"]) + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "report_id": report_id,
                "block_type": block_type,
                "data": evidence_data,
                "previous_hash": last["current_hash"],
            }
            b["current_hash"] = self.calculate_hash(b)
            self.chain.append(b)
            self._save_chain()
            return b

    def verify_chain(self) -> Dict[str, Any]:
        if not self.chain: return {"valid": False, "message": "Evidence chain is empty.", "checked_blocks": 0, "invalid_block": None}
        for i, b in enumerate(self.chain):
            if b.get("block_index") != i: return {"valid": False, "message": "Block index mismatch.", "checked_blocks": i, "invalid_block": i}
            if self.calculate_hash(b) != b.get("current_hash"): return {"valid": False, "message": "Block hash mismatch. The block data may have been modified.", "checked_blocks": i, "invalid_block": i}
            if i == 0:
                if b.get("previous_hash") != "0": return {"valid": False, "message": "Invalid genesis block.", "checked_blocks": 1, "invalid_block": 0}
            elif b.get("previous_hash") != self.chain[i - 1].get("current_hash"):
                return {"valid": False, "message": "Previous hash linkage failed.", "checked_blocks": i, "invalid_block": i}
        return {"valid": True, "message": "Evidence chain is valid.", "checked_blocks": len(self.chain), "invalid_block": None, "latest_hash": self.chain[-1]["current_hash"]}

    def find_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        for b in self.chain:
            if b.get("report_id") == report_id: return b
        return None

    def get_chain(self) -> List[Dict[str, Any]]: return list(self.chain)

    def get_chain_info(self) -> Dict[str, Any]:
        v = self.verify_chain()
        last = self.get_latest_block()
        return {
            "chain_valid": v["valid"],
            "total_blocks": len(self.chain),
            "latest_block_index": last.get("block_index") if last else None,
            "latest_hash": last.get("current_hash") if last else None,
            "storage_file": os.path.basename(self.storage_path),
            "verification": v,
        }
