#!/usr/bin/env python3
"""
Evidence Chain Migration Script
Harvest Harbor — AI Crop Disease Detection & Traceability Platform

Safely migrates historical evidence_chain.json by:
1. Creating a backup at evidence_chain.json.pre_migration_backup.
2. Sanitizing any embedded absolute filesystem paths across all blocks.
3. Recalculating block hashes sequentially to preserve cryptographic linkage.
4. Appending a signed migration block documenting the audit action.
5. Verifying complete chain cryptographic validity before atomic save.
6. Being fully idempotent.
"""

import os
import sys
import json
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from traceability.blockchain import EvidenceBlockchain
from app import remove_absolute_path_keys

CHAIN_PATH = BASE_DIR / "traceability" / "evidence_chain.json"
BACKUP_PATH = BASE_DIR / "traceability" / "evidence_chain.json.pre_migration_backup"


def contains_unredacted_paths(data_obj) -> bool:
    """Check if object contains any absolute filesystem path strings or keys."""
    raw_str = json.dumps(data_obj)
    suspicious = ["/Users/", "/home/", "/private/", "/var/", "absolute_path"]
    return any(s in raw_str for s in suspicious)


def migrate_chain(force: bool = False) -> bool:
    if not CHAIN_PATH.exists():
        print(f"[INFO] Evidence chain file does not exist at {CHAIN_PATH}. Nothing to migrate.")
        return True

    print(f"[INFO] Loading evidence chain from: {CHAIN_PATH}")
    with open(CHAIN_PATH, "r", encoding="utf-8") as f:
        chain = json.load(f)

    if not isinstance(chain, list) or len(chain) == 0:
        print("[ERROR] Evidence chain is empty or invalid format.")
        return False

    has_unredacted = any(contains_unredacted_paths(b.get("data", {})) for b in chain)
    already_migrated = any(b.get("block_type") == "chain_migration" for b in chain)

    if not has_unredacted and already_migrated and not force:
        print("[INFO] Evidence chain has already been migrated and contains no unredacted paths. Idempotent skip.")
        blockchain = EvidenceBlockchain(storage_path=str(CHAIN_PATH))
        verification = blockchain.verify_chain()
        print(f"[INFO] Chain validity: {verification['valid']} ({verification['checked_blocks']} blocks checked)")
        return verification["valid"]

    # 1. Backup pre-migration chain
    if not BACKUP_PATH.exists() or force:
        print(f"[INFO] Creating backup at: {BACKUP_PATH}")
        shutil.copy2(CHAIN_PATH, BACKUP_PATH)
    else:
        print(f"[INFO] Pre-migration backup already exists at: {BACKUP_PATH}")

    print(f"[INFO] Migrating {len(chain)} blocks...")

    # 2. Sanitize each block's data and recalculate hashes sequentially
    for i, block in enumerate(chain):
        if "data" in block and isinstance(block["data"], dict):
            block["data"] = remove_absolute_path_keys(block["data"])
        if "evidence_data" in block and isinstance(block["evidence_data"], dict):
            block["evidence_data"] = remove_absolute_path_keys(block["evidence_data"])

        # Linkage
        if i == 0:
            block["previous_hash"] = "0"
        else:
            block["previous_hash"] = chain[i - 1]["current_hash"]

        block["current_hash"] = EvidenceBlockchain.calculate_hash(block)

    # 3. Append signed migration block
    migration_id = f"MIGRATION-{uuid.uuid4().hex[:8].upper()}"
    migration_block = {
        "block_index": len(chain),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_id": migration_id,
        "block_type": "chain_migration",
        "data": {
            "migration_timestamp": datetime.now(timezone.utc).isoformat(),
            "migrated_blocks_count": len(chain),
            "migration_reason": "Sanitized absolute filesystem paths from historical evidence chain",
            "sanitizer_version": "v2",
        },
        "previous_hash": chain[-1]["current_hash"],
    }
    migration_block["current_hash"] = EvidenceBlockchain.calculate_hash(migration_block)
    chain.append(migration_block)

    # 4. In-memory validation before write
    temp_chain_path = str(CHAIN_PATH) + ".migration_tmp"
    with open(temp_chain_path, "w", encoding="utf-8") as f:
        json.dump(chain, f, indent=2, ensure_ascii=False)

    test_bc = EvidenceBlockchain(storage_path=temp_chain_path)
    verification = test_bc.verify_chain()

    if not verification["valid"]:
        print(f"[ERROR] Migration failed verification check: {verification}")
        if os.path.exists(temp_chain_path):
            os.remove(temp_chain_path)
        return False

    # 5. Atomic replace
    os.replace(temp_chain_path, CHAIN_PATH)
    print(f"[SUCCESS] Evidence chain successfully migrated!")
    print(f"[SUCCESS] Total blocks in chain: {len(chain)}")
    print(f"[SUCCESS] Cryptographic verification: PASS (checked {verification['checked_blocks']} blocks)")
    return True


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    success = migrate_chain(force=force_run)
    sys.exit(0 if success else 1)
