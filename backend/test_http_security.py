"""
Harvest Harbor — Real HTTP Security Test Suite
================================================
Tests real HTTP request handling (headers, status codes, RBAC, path traversal, asset downloads)
via direct ASGI request dispatching against FastAPI app.

Test Coverage:
  1. 401 without auth (unauthenticated asset / endpoint request)
  2. 403 wrong role (farmer attempting agronomist-only endpoint)
  3. 200 correct role (agronomist accessing protected endpoint)
  4. 403 path traversal (attempting ../ path traversal on /uploads and /generated)
  5. 404 missing asset (requesting nonexistent file from /uploads)
  6. Authenticated image download (verifying successful 200 binary response with headers)
  7. Query token rejection (verifying ?token=... is ignored/rejected without headers)
"""

import asyncio
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

# Set testing environment before importing app modules
os.environ["ENVIRONMENT"] = "testing"
os.environ.setdefault("KERAS_HOME", tempfile.mkdtemp())

from app import app, startup_event, UPLOADS_DIR, GENERATED_DIR

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
                response_start["status"] = message["status"]
                response_start["headers"] = {
                    k.decode("utf-8").lower(): v.decode("utf-8")
                    for k, v in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.app(scope, receive, send))

        status_code = response_start.get("status", 500)
        response_headers = response_start.get("headers", {})
        response_body = b"".join(body_parts)

        return status_code, response_headers, response_body

    def get(self, path: str, headers: dict = None, query_string: str = ""):
        return self.request("GET", path, headers=headers, query_string=query_string)


class TestHTTPSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            startup_event()
        except Exception as e:
            print("Startup exception (ignored):", e)
        cls.client = ASGITestClient(app)

        # Create a sample test image inside UPLOADS_DIR for download tests
        cls.test_filename = "test_auth_download_sample.jpg"
        cls.test_file_path = Path(UPLOADS_DIR) / cls.test_filename
        cls.test_image_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08"
        with open(cls.test_file_path, "wb") as f:
            f.write(cls.test_image_data)

    @classmethod
    def tearDownClass(cls):
        if cls.test_file_path.exists():
            try:
                cls.test_file_path.unlink()
            except Exception:
                pass

    def test_401_without_auth(self):
        """Requesting protected asset/endpoint without auth headers returns 401 Unauthorized."""
        status, headers, body = self.client.get(f"/uploads/{self.test_filename}")
        self.assertEqual(status, 401, f"Expected 401 without auth headers, got {status}")
        
        status, headers, body = self.client.get("/review-queue")
        self.assertEqual(status, 401, f"Expected 401 for /review-queue without auth headers, got {status}")

    def test_403_wrong_role(self):
        """Farmer role attempting agronomist-only endpoint (/review-queue) returns 403 Forbidden."""
        auth_headers = {
            "Authorization": "Bearer dev-farmer-key",
            "X-User-Role": "farmer",
        }
        status, headers, body = self.client.get("/review-queue", headers=auth_headers)
        self.assertEqual(status, 403, f"Expected 403 Forbidden for farmer role on /review-queue, got {status}")

    def test_200_correct_role(self):
        """Agronomist role with valid credentials successfully accesses /review-queue (200 OK)."""
        auth_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, headers, body = self.client.get("/review-queue", headers=auth_headers)
        self.assertEqual(status, 200, f"Expected 200 OK for agronomist role on /review-queue, got {status}")
        data = json.loads(body.decode("utf-8"))
        self.assertTrue(data.get("success"))

    def test_403_path_traversal(self):
        """Attempting path traversal on /uploads or /generated returns 403 Forbidden."""
        auth_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, headers, body = self.client.get("/uploads/../app.py", headers=auth_headers)
        self.assertEqual(status, 403, f"Expected 403 Forbidden for path traversal on /uploads, got {status}")

        status, headers, body = self.client.get("/generated/../config.py", headers=auth_headers)
        self.assertEqual(status, 403, f"Expected 403 Forbidden for path traversal on /generated, got {status}")

    def test_404_missing_asset(self):
        """Requesting nonexistent asset with valid credentials returns 404 Not Found."""
        auth_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, headers, body = self.client.get("/uploads/nonexistent_sample_99999.jpg", headers=auth_headers)
        self.assertEqual(status, 404, f"Expected 404 Not Found for missing asset, got {status}")

    def test_authenticated_image_download(self):
        """Authenticated request to /uploads/{filename} downloads real image binary stream (200 OK)."""
        auth_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, headers, body = self.client.get(f"/uploads/{self.test_filename}", headers=auth_headers)
        self.assertEqual(status, 200, f"Expected 200 OK for authenticated image download, got {status}")
        self.assertEqual(body, self.test_image_data, "Downloaded image binary content does not match original file")

    def test_query_token_param_rejected(self):
        """Passing API key via ?token=... without Authorization header returns 401 Unauthorized."""
        status, headers, body = self.client.get(
            f"/uploads/{self.test_filename}",
            query_string="token=dev-agronomist-key"
        )
        self.assertEqual(status, 401, f"Query parameter ?token=... must be rejected (401), got {status}")

    def test_security_headers_include_csp_and_permissions_policy(self):
        """Responses must include Content-Security-Policy and Permissions-Policy headers."""
        status, headers, _ = self.client.get("/health")
        self.assertEqual(status, 200)
        self.assertIn("content-security-policy", headers)
        self.assertIn("permissions-policy", headers)
        self.assertIn("frame-ancestors 'none'", headers["content-security-policy"])

    def test_extension_content_mismatch_rejected(self):
        """Uploading a JPEG image with .png extension or mismatched MIME must be rejected with 400."""
        boundary = "----WebKitFormBoundaryMismatchTest"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="leaf.png"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + self.test_image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-API-Key": "dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, _, resp_body = self.client.request("POST", "/predict", headers=headers, body=body)
        self.assertEqual(status, 400)
        self.assertIn("does not match", resp_body.decode("utf-8"))


    def test_saved_upload_extension_normalized_to_jpg(self):
        """Uploading a valid PNG image should have its saved disk extension normalized to .jpg."""
        png_io = io.BytesIO()
        img = Image.new("RGB", (100, 100), color=(34, 139, 34))
        img.save(png_io, format="PNG")
        png_bytes = png_io.getvalue()

        boundary = "----WebKitFormBoundaryPngNormTest"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="sample_leaf.png"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode("utf-8") + png_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-API-Key": "dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, _, resp_body = self.client.request("POST", "/predict", headers=headers, body=body)
        self.assertEqual(status, 200)
        data = json.loads(resp_body.decode("utf-8"))
        self.assertIn("image", data)
        self.assertIn("url", data["image"])
        self.assertTrue(data["image"]["url"].endswith(".jpg"), f"Expected .jpg URL, got {data['image']['url']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

