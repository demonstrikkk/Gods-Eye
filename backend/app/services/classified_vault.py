from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger("classified_vault")


class ClassifiedVaultService:
    """Local-only encrypted store for classified payloads and deterministic query."""

    def __init__(
        self,
        vault_path: Optional[Path] = None,
        encryption_key: Optional[str] = None,
        strict_local_only: Optional[bool] = None,
    ):
        configured_path = (settings.CLASSIFIED_VAULT_PATH or "").strip()
        if vault_path is not None:
            self._vault_path = vault_path
        elif configured_path:
            path = Path(configured_path)
            if not path.is_absolute():
                path = Path(__file__).resolve().parent.parent.parent / configured_path
            self._vault_path = path
        else:
            self._vault_path = Path(__file__).resolve().parent.parent / "data" / "classified_vault.json"

        self._encryption_key = (encryption_key if encryption_key is not None else settings.CLASSIFIED_VAULT_KEY).strip()
        self._strict_local_only = settings.CLASSIFIED_STRICT_LOCAL_ONLY if strict_local_only is None else strict_local_only
        self._lock = RLock()

    def _assert_local_mode(self):
        if self._strict_local_only and not settings.LOCAL_MODE_ENABLED:
            raise RuntimeError("Classified vault is available only in local sovereign mode.")

    def _cipher(self) -> Fernet:
        if not self._encryption_key:
            raise RuntimeError("CLASSIFIED_VAULT_KEY is required for classified data encryption.")

        try:
            return Fernet(self._encryption_key.encode("utf-8"))
        except Exception as exc:
            raise RuntimeError("CLASSIFIED_VAULT_KEY is invalid. Provide a valid Fernet key.") from exc

    def _ensure_parent(self):
        self._vault_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_records(self) -> List[Dict[str, Any]]:
        if not self._vault_path.exists():
            return []
        try:
            payload = json.loads(self._vault_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
            return []
        except Exception as exc:
            logger.error("Failed loading classified vault: %s", exc)
            raise RuntimeError(f"Corrupted or inaccessible classified vault: {exc}") from exc

    def _save_records(self, records: List[Dict[str, Any]]):
        self._ensure_parent()
        self._vault_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token for token in re.split(r"[^a-zA-Z0-9]+", (text or "").lower()) if token]

    @staticmethod
    def _sentence_snippets(text: str, keywords: List[str], limit: int = 2) -> List[str]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        if not keywords:
            return sentences[:limit]
        selected: List[str] = []
        for sentence in sentences:
            s_lower = sentence.lower()
            if any(keyword in s_lower for keyword in keywords):
                selected.append(sentence)
                if len(selected) >= limit:
                    break
        return selected or sentences[:limit]

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            self._assert_local_mode()
            records = self._load_records()
            return {
                "records": len(records),
                "local_mode_enabled": settings.LOCAL_MODE_ENABLED,
                "strict_local_only": self._strict_local_only,
                "encrypted_at_rest": bool(self._encryption_key),
                "vault_path": str(self._vault_path),
                "llm_provider": settings.LOCAL_LLM_PROVIDER,
                "llm_model": settings.LOCAL_LLM_MODEL,
            }

    def ingest(
        self,
        source_id: str,
        classification: str,
        text: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            self._assert_local_mode()
            cipher = self._cipher()
            records = self._load_records()

            normalized_tags = sorted({str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()})
            timestamp = self._utc_now_iso()
            plaintext = (text or "").strip()
            ciphertext = cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")
            content_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()

            record = {
                "id": f"cls-{uuid4().hex[:16]}",
                "source_id": str(source_id).strip() or "unknown",
                "classification": str(classification).strip() or "CONFIDENTIAL",
                "tags": normalized_tags,
                "metadata": metadata or {},
                "ciphertext": ciphertext,
                "content_hash": content_hash,
                "created_at": timestamp,
                "updated_at": timestamp,
            }

            records.append(record)
            self._save_records(records)

            return {
                "id": record["id"],
                "source_id": record["source_id"],
                "classification": record["classification"],
                "tags": record["tags"],
                "content_hash": record["content_hash"],
                "created_at": record["created_at"],
            }

    def query(
        self,
        query_text: str,
        classification: Optional[str] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        with self._lock:
            self._assert_local_mode()
            cipher = self._cipher()
            records = self._load_records()

            normalized_query = (query_text or "").strip().lower()
            keywords = self._tokenize(normalized_query)
            wanted_tags = {str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()}
            classification_filter = (classification or "").strip().lower()

            matches: List[Dict[str, Any]] = []
            for record in records:
                if classification_filter and str(record.get("classification", "")).lower() != classification_filter:
                    continue
                record_tags = {str(tag).strip().lower() for tag in record.get("tags", [])}
                if wanted_tags and not wanted_tags.issubset(record_tags):
                    continue

                try:
                    plaintext = cipher.decrypt(str(record.get("ciphertext", "")).encode("utf-8")).decode("utf-8")
                except (InvalidToken, ValueError, TypeError):
                    continue

                lowered = plaintext.lower()
                score = 0
                for keyword in keywords:
                    score += lowered.count(keyword)
                if normalized_query and score == 0 and normalized_query not in lowered:
                    continue

                snippets = self._sentence_snippets(plaintext, keywords)
                matches.append(
                    {
                        "id": record.get("id"),
                        "source_id": record.get("source_id"),
                        "classification": record.get("classification"),
                        "tags": record.get("tags", []),
                        "score": score,
                        "snippets": snippets,
                        "created_at": record.get("created_at"),
                    }
                )

            matches.sort(key=lambda item: (item.get("score", 0), item.get("created_at", "")), reverse=True)
            top_matches = matches[: max(1, int(top_k))]

            if not top_matches:
                answer = "No relevant classified records matched the local query."
            else:
                answer_lines = [f"Matched {len(top_matches)} classified records in local vault."]
                for item in top_matches:
                    snippet = item["snippets"][0] if item["snippets"] else "No snippet available."
                    answer_lines.append(
                        f"- {item['id']} ({item['classification']} | score={item['score']}): {snippet}"
                    )
                answer = "\n".join(answer_lines)

            return {
                "answer": answer,
                "matches": top_matches,
                "inference": {
                    "mode": "local_deterministic_ranker",
                    "provider": settings.LOCAL_LLM_PROVIDER,
                    "model": settings.LOCAL_LLM_MODEL,
                    "remote_calls": False,
                },
            }

    def delete_record(self, record_id: str) -> bool:
        with self._lock:
            self._assert_local_mode()
            records = self._load_records()
            original_count = len(records)
            remaining = [record for record in records if str(record.get("id")) != str(record_id)]
            if len(remaining) == original_count:
                return False
            self._save_records(remaining)
            return True

    def purge(self, source_id: Optional[str] = None) -> int:
        with self._lock:
            self._assert_local_mode()
            records = self._load_records()
            if source_id:
                remaining = [record for record in records if str(record.get("source_id")) != str(source_id)]
            else:
                remaining = []
            deleted = len(records) - len(remaining)
            self._save_records(remaining)
            return deleted


_vault_service: ClassifiedVaultService | None = None


def get_classified_vault_service() -> ClassifiedVaultService:
    global _vault_service
    if _vault_service is None:
        _vault_service = ClassifiedVaultService()
    return _vault_service
