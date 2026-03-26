import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints.classified import router as classified_router
from app.services.classified_vault import ClassifiedVaultService


app = FastAPI()
app.include_router(classified_router, prefix="/api/v1/classified")


class ClassifiedEndpointsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._vault_path = Path(self._tmp_dir.name) / "classified_vault.json"
        self._service = ClassifiedVaultService(
            vault_path=self._vault_path,
            encryption_key=Fernet.generate_key().decode("utf-8"),
            strict_local_only=False,
        )

        import app.api.endpoints.classified as classified_endpoint_module

        self._orig_get_service = classified_endpoint_module.get_classified_vault_service
        classified_endpoint_module.get_classified_vault_service = lambda: self._service

    def tearDown(self):
        import app.api.endpoints.classified as classified_endpoint_module

        classified_endpoint_module.get_classified_vault_service = self._orig_get_service
        self._tmp_dir.cleanup()

    def test_ingest_and_query_roundtrip(self):
        ingest_response = self.client.post(
            "/api/v1/classified/ingest",
            json={
                "source_id": "field-report-alpha",
                "classification": "SECRET",
                "text": "Fuel depot shortage near corridor east. Reinforcements delayed by storms.",
                "tags": ["logistics", "corridor"],
                "metadata": {"operator": "unit-17"},
            },
        )

        self.assertEqual(ingest_response.status_code, 200)
        ingest_body = ingest_response.json()
        self.assertEqual(ingest_body["status"], "success")
        record_id = ingest_body["data"]["id"]

        query_response = self.client.post(
            "/api/v1/classified/query",
            json={
                "query": "fuel shortage corridor",
                "classification": "SECRET",
                "tags": ["logistics"],
                "top_k": 3,
            },
        )

        self.assertEqual(query_response.status_code, 200)
        query_body = query_response.json()
        self.assertEqual(query_body["status"], "success")
        self.assertGreaterEqual(len(query_body["data"]["matches"]), 1)
        self.assertEqual(query_body["data"]["matches"][0]["id"], record_id)
        self.assertEqual(query_body["data"]["inference"]["remote_calls"], False)

    def test_delete_and_purge(self):
        first = self.client.post(
            "/api/v1/classified/ingest",
            json={
                "source_id": "src-a",
                "classification": "CONFIDENTIAL",
                "text": "Record one for deletion tests.",
                "tags": ["a"],
                "metadata": {},
            },
        ).json()["data"]["id"]

        second = self.client.post(
            "/api/v1/classified/ingest",
            json={
                "source_id": "src-b",
                "classification": "CONFIDENTIAL",
                "text": "Record two for deletion tests.",
                "tags": ["b"],
                "metadata": {},
            },
        ).json()["data"]["id"]

        delete_response = self.client.delete(f"/api/v1/classified/record/{first}")
        self.assertEqual(delete_response.status_code, 200)

        missing_response = self.client.delete(f"/api/v1/classified/record/{first}")
        self.assertEqual(missing_response.status_code, 404)

        purge_response = self.client.delete("/api/v1/classified/records?source_id=src-b")
        self.assertEqual(purge_response.status_code, 200)
        self.assertEqual(purge_response.json()["deleted"], 1)

        query_response = self.client.post(
            "/api/v1/classified/query",
            json={"query": "Record", "top_k": 5},
        )
        self.assertEqual(query_response.status_code, 200)
        self.assertEqual(query_response.json()["data"]["matches"], [])


if __name__ == "__main__":
    unittest.main()
