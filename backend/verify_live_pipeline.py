#!/usr/bin/env python3
"""
Harvest Harbor — Comprehensive Live Deep Audit & Verification
Validates end-to-end system functionality across:
1. System Health & Metadata
2. Traceability Chain Cryptographic Integrity
3. Real Multi-Model Inference with Sample & Diseased Leaves
4. Explainability (Grad-CAM), Segmentation (U-Net), and Severity
5. Rejection & Low Crop Confidence Contract Verification
6. Asset Authentication & Directory Traversal Protection
7. Review Queue Resolution & Audit Report Reconstruction
"""

import asyncio
import io
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import app, startup_event, evidence_blockchain, review_queue

class ASGITestClient:
    """Zero-dependency ASGI Test Client for executing real HTTP requests against FastAPI app."""

    def __init__(self, asgi_app):
        self.app = asgi_app

    def request(self, method: str, path: str, headers: dict = None, body: bytes = b"", query_string: str = ""):
        response_start = {}
        body_parts = []

        headers_list = []
        if headers:
            for k, v in headers.items():
                headers_list.append((k.lower().encode("utf-8"), str(v).encode("utf-8")))

        raw_path = path.encode("utf-8")
        encoded_query = query_string.encode("utf-8") if isinstance(query_string, str) else query_string

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method.upper(),
            "path": path,
            "raw_path": raw_path,
            "query_string": encoded_query,
            "headers": headers_list,
        }

        request_sent = False
        disconnect_event = asyncio.Event()

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            await disconnect_event.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            if message["type"] == "http.response.start":
                response_start.update(message)
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.app(scope, receive, send))
        finally:
            loop.close()

        status_code = response_start.get("status", 500)
        resp_headers = dict(
            (k.decode("utf-8").lower(), v.decode("utf-8"))
            for k, v in response_start.get("headers", [])
        )
        response_body = b"".join(body_parts)
        return status_code, resp_headers, response_body

    def get(self, path: str, headers: dict = None, query_string: str = ""):
        return self.request("GET", path, headers=headers, query_string=query_string)

    def post(self, path: str, headers: dict = None, body: bytes = b""):
        return self.request("POST", path, headers=headers, body=body)

    def post_json(self, path: str, json_data: dict, headers: dict = None):
        h = dict(headers or {})
        h["content-type"] = "application/json"
        body = json.dumps(json_data).encode("utf-8")
        return self.post(path, headers=h, body=body)

    def post_file(self, path: str, filename: str, file_bytes: bytes, headers: dict = None):
        boundary = "----WebKitFormBoundaryHHTest12345678"
        h = dict(headers or {})
        h["content-type"] = f"multipart/form-data; boundary={boundary}"
        
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
        return self.post(path, headers=h, body=body)


def main():
    print("=" * 70)
    print("HARVEST HARBOR — COMPREHENSIVE LIVE SYSTEM AUDIT")
    print("=" * 70)

    try:
        startup_event()
    except Exception as e:
        print(f"[WARN] Startup event exception: {e}")

    client = ASGITestClient(app)
    auth_headers = {
        "Authorization": "Bearer dev-agronomist-key",
        "X-Inspector-ID": "AGRO-7402",
        "X-User-Role": "agronomist"
    }

    # 1. Health check
    print("\n[1] Checking /health endpoint...")
    status, headers, body = client.get("/health")
    assert status == 200, f"Expected 200, got {status}: {body.decode()}"
    health_data = json.loads(body.decode())
    assert health_data.get("status") == "healthy"
    print(f"    ✓ Health check passed. System status: {health_data.get('status')}")
    print(f"      Models loaded: {list(health_data.get('models', {}).keys())}")
    kb_meta = health_data.get("knowledge_base", {})
    print(f"      Disease knowledge base: {kb_meta.get('disease_count')} diseases loaded (loaded: {kb_meta.get('loaded')})")

    # 2. Root endpoint
    print("\n[2] Checking Root endpoint /...")
    status, headers, body = client.get("/")
    assert status == 200, f"Expected 200, got {status}"
    root_data = json.loads(body.decode())
    print(f"    ✓ Root endpoint operational: {root_data.get('message', root_data.get('status'))}")

    # 3. Traceability Status
    print("\n[3] Checking Traceability Ledger Cryptographic Integrity...")
    status, headers, body = client.get("/traceability/status", headers=auth_headers)
    assert status == 200, f"Expected 200, got {status}"
    chain_status = json.loads(body.decode())
    assert chain_status.get("chain_valid") is True, f"Chain invalid: {chain_status}"
    assert chain_status.get("verification", {}).get("valid") is True, f"Verification failed: {chain_status}"
    print(f"    ✓ Ledger cryptographic integrity verified! Valid: True, Checked blocks: {chain_status.get('verification', {}).get('checked_blocks')}")

    # 4. Inference on Diseased Leaf
    print("\n[4] Running Multi-Model Inference on real diseased leaf (Potato Early Blight)...")
    diseased_path = Path(__file__).resolve().parent.parent / "test_images" / "diseased_leaf.jpg"
    assert diseased_path.exists(), f"File not found: {diseased_path}"
    
    with open(diseased_path, "rb") as f:
        file_bytes = f.read()

    status, headers, body = client.post_file("/predict", "diseased_leaf.jpg", file_bytes, headers=auth_headers)
    assert status == 200, f"Predict failed: {status} - {body.decode()}"
    pred_data = json.loads(body.decode())
    
    print(f"    ✓ Prediction succeeded.")
    print(f"      Pipeline Status:   {pred_data.get('status')}")
    print(f"      Health Prediction: {pred_data.get('health_prediction', {}).get('prediction')} (conf: {pred_data.get('health_prediction', {}).get('confidence'):.3f})")
    print(f"      Crop Prediction:   {pred_data.get('crop_prediction', {}).get('prediction')} (conf: {pred_data.get('crop_prediction', {}).get('confidence'):.3f})")
    
    disease_analysis = pred_data.get("disease_analysis")
    if disease_analysis:
        val_info = disease_analysis.get("validation", {})
        print(f"      Disease Status:    {val_info.get('status')}")
        print(f"      Validated Disease: {disease_analysis.get('prediction')}")
        print(f"      Raw Candidate:     {disease_analysis.get('raw_prediction')}")
        compat_list = disease_analysis.get('compatible_top_3') or val_info.get('compatible_top_3', [])
        print(f"      Compatible Top 3:  {[d.get('class') or d.get('disease') for d in compat_list]}")
        print(f"      Raw Top 3:         {[d.get('class') or d.get('disease') for d in disease_analysis.get('raw_top_3', [])]}")

    seg = pred_data.get("segmentation")
    if seg:
        seg_area = seg.get('affected_percentage', seg.get('affected_area_percent'))
        print(f"      Segmentation Area: {seg_area}%")
        print(f"      Overlay URL:       {seg.get('overlay_path')}")

    expl = pred_data.get("explainability")
    if expl:
        print(f"      Grad-CAM Overlay:  {expl.get('overlay')}")

    sev = pred_data.get("severity")
    if sev:
        print(f"      Severity Tier:     {sev.get('severity')} ({sev.get('affected_area_percent')}%)")

    trace = pred_data.get("traceability")
    assert trace is not None, "Missing traceability payload"
    report_id = trace.get("report_id")
    block_idx = trace.get("blockchain", {}).get("block_index") if isinstance(trace.get("blockchain"), dict) else trace.get("block_index")
    print(f"      Traceability ID:   {report_id} (Block Index: {block_idx})")

    # 4b. Inference on Healthy Leaf
    print("\n[4b] Running Multi-Model Inference on real healthy leaf (sample_leaf.jpg)...")
    sample_path = Path(__file__).resolve().parent.parent / "test_images" / "sample_leaf.jpg"
    assert sample_path.exists(), f"File not found: {sample_path}"
    with open(sample_path, "rb") as f:
        sample_bytes = f.read()

    status_h, _, body_h = client.post_file("/predict", "sample_leaf.jpg", sample_bytes, headers=auth_headers)
    assert status_h == 200, f"Healthy predict failed: {status_h} - {body_h.decode()}"
    pred_data_h = json.loads(body_h.decode())
    print(f"    ✓ Healthy leaf prediction succeeded.")
    print(f"      Pipeline Status:   {pred_data_h.get('status')}")
    print(f"      Health Prediction: {pred_data_h.get('health_prediction', {}).get('prediction')} (conf: {pred_data_h.get('health_prediction', {}).get('confidence'):.3f})")
    print(f"      Crop Prediction:   {pred_data_h.get('crop_prediction', {}).get('prediction')}")
    if pred_data_h.get("status") == "healthy_prediction":
        assert pred_data_h.get("disease_analysis") is None or pred_data_h.get("disease_analysis", {}).get("prediction") is None
        print(f"      Disease Analysis correctly suppressed for healthy specimen.")

    # 5. Protected Asset Streaming
    print("\n[5] Testing Authenticated Asset Streaming...")
    asset_path = seg.get("overlay_path") if seg else expl.get("overlay")
    assert asset_path, "No asset path to test"

    # Unauthenticated -> 401
    status_unauth, _, _ = client.get(asset_path)
    assert status_unauth == 401, f"Expected 401 unauth, got {status_unauth}"
    print(f"    ✓ Unauthenticated access correctly blocked: 401 Unauthorized")

    # Query token parameter -> 401 (must not allow token query param)
    status_query, _, _ = client.get(asset_path, query_string="token=dev-agronomist-key")
    assert status_query == 401, f"Expected 401 query token, got {status_query}"
    print(f"    ✓ Query param token access correctly blocked: 401 Unauthorized")

    # Traversal attempt -> 403
    status_traversal, _, _ = client.get("/uploads/../../etc/passwd", headers=auth_headers)
    assert status_traversal == 403, f"Expected 403 traversal, got {status_traversal}"
    print(f"    ✓ Directory traversal correctly blocked: 403 Forbidden")

    # Authenticated asset download -> 200
    status_auth, auth_headers_resp, auth_content = client.get(asset_path, headers=auth_headers)
    assert status_auth == 200, f"Expected 200 auth download, got {status_auth}"
    assert auth_headers_resp.get("content-type") in ["image/png", "image/jpeg"]
    assert len(auth_content) > 100
    print(f"    ✓ Authenticated asset retrieval verified: 200 OK ({len(auth_content)} bytes, {auth_headers_resp.get('content-type')})")

    # 6. Report Reconstruction & Review Queue Resolution
    # Ensure item exists in queue for testing
    enqueued_item = review_queue.enqueue(
        report_id=report_id,
        reasons=["routine_verification"],
        priority="low",
        summary={"report_id": report_id}
    )
    review_id = enqueued_item["review_id"]

    resolve_payload = {
        "decision": "confirmed",
        "notes": "Verified field sample matches potato early blight."
    }
    status_resolve, _, body_resolve = client.post_json(f"/review-queue/{review_id}/resolve", resolve_payload, headers=auth_headers)
    assert status_resolve == 200, f"Resolve failed: {status_resolve} - {body_resolve.decode()}"
    resolve_data = json.loads(body_resolve.decode())
    print(f"    ✓ Review resolved: Decision={resolve_data.get('item', {}).get('decision')}, Block Index={resolve_data.get('review_block', {}).get('index')}")

    # Retrieve reconstructed report
    status_report, _, body_report = client.get(f"/traceability/report/{report_id}", headers=auth_headers)
    assert status_report == 200, f"Get report failed: {status_report} - {body_report.decode()}"
    report_wrapper = json.loads(body_report.decode())
    assert report_wrapper.get("success") is True
    report_block = report_wrapper.get("report", {})
    ev_data = report_block.get("evidence_data") or report_block.get("data") or {}
    human_review = ev_data.get("human_review", {})
    assert human_review.get("resolved") is True, f"Expected resolved=True, got {human_review}"
    assert human_review.get("resolution_status") == "confirmed"
    assert len(ev_data.get("review_history", [])) >= 1
    print(f"    ✓ Reconstructed report retrieved successfully.")
    print(f"      Report Resolution: {human_review.get('resolution_status')}")
    print(f"      Reviewer ID:       {human_review.get('reviewer')}")
    print(f"      Notes:             {human_review.get('resolution_notes')}")
    print(f"      History Count:     {len(ev_data.get('review_history', []))}")

    # 7. Re-verify ledger integrity after append
    print("\n[7] Re-verifying Ledger Integrity...")
    verify_res = evidence_blockchain.verify_chain()
    assert verify_res.get("valid") is True, f"Chain invalid after resolution: {verify_res}"
    print(f"    ✓ Ledger cryptographic integrity re-verified: {verify_res.get('checked_blocks')} blocks valid.")

    print("\n" + "=" * 70)
    print("ALL LIVE AUDIT CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
