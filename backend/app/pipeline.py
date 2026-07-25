import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from .config import Settings
from .models import GenerationRequest, ProvenanceRecord
from .repository import ProvenanceRepository, utcnow


def _jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return value
    return json.loads(json.dumps(value, default=lambda item: getattr(item, "__dict__", str(item))))


class TraceFramePipeline:
    def __init__(self, settings: Settings, repository: ProvenanceRepository):
        self.settings = settings
        self.repository = repository
        settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    def generate(self, request: GenerationRequest, parent_id: str | None = None) -> ProvenanceRecord:
        record = ProvenanceRecord(
            id=f"run_{uuid.uuid4().hex[:12]}",
            parent_id=parent_id,
            prompt=request.prompt,
            provider="openai",
            model=self.settings.openai_image_model,
            params={"size": request.size, "quality": request.quality},
            status="running",
            created_at=utcnow(),
        )
        self.repository.save(record)
        try:
            if self.settings.live_ready and not self.settings.demo_mode:
                record = self._generate_live(record)
            else:
                record = self._generate_demo(record)
        except Exception as exc:
            record.status = "failed"
            record.completed_at = utcnow()
            record.error = f"{type(exc).__name__}: {exc}"
        return self.repository.save(record)

    def _generate_live(self, record: ProvenanceRecord) -> ProvenanceRecord:
        from genblaze_core import KeyStrategy, Modality, ObjectStorageSink, Pipeline
        from genblaze_openai import DalleProvider
        from genblaze_s3 import S3StorageBackend

        storage = ObjectStorageSink(
            S3StorageBackend.for_backblaze(
                self.settings.b2_bucket,
                region=self.settings.b2_region,
                key_id=self.settings.b2_key_id,
                app_key=self.settings.b2_app_key,
            ),
            key_strategy=KeyStrategy.HIERARCHICAL,
            prefix="traceframe",
        )
        result = (
            Pipeline("traceframe-image")
            .step(
                DalleProvider(api_key=self.settings.openai_api_key),
                model=record.model,
                prompt=record.prompt,
                modality=Modality.IMAGE,
                **record.params,
            )
            .run(sink=storage, timeout=180)
        )
        asset = result.run.steps[0].assets[0]
        record.status = "completed"
        record.completed_at = utcnow()
        record.asset_url = asset.url
        record.asset_sha256 = asset.sha256
        record.manifest_sha256 = result.manifest.canonical_hash
        record.manifest_url = getattr(result.manifest, "manifest_uri", None)
        self._save_manifest(record.id, _jsonable(result.manifest))
        return record

    def _generate_demo(self, record: ProvenanceRecord) -> ProvenanceRecord:
        source = Path("public/og.png")
        destination = self.settings.artifacts_path / f"{record.id}.png"
        if source.exists():
            shutil.copyfile(source, destination)
        else:
            destination.write_bytes(b"TraceFrame demo artifact")
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        manifest = {
            "schema": "traceframe.provenance/v1",
            "run_id": record.id,
            "parent_run_id": record.parent_id,
            "provider": record.provider,
            "model": record.model,
            "prompt": record.prompt,
            "params": record.params,
            "created_at": record.created_at.isoformat(),
            "asset": {"url": f"/artifacts/{destination.name}", "sha256": digest},
        }
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        record.status = "completed"
        record.completed_at = utcnow()
        record.asset_url = f"/artifacts/{destination.name}"
        record.asset_sha256 = digest
        record.manifest_sha256 = hashlib.sha256(canonical).hexdigest()
        record.manifest_url = f"/manifests/{record.id}.json"
        self._save_manifest(record.id, {**manifest, "canonical_hash": record.manifest_sha256})
        return record

    def _save_manifest(self, record_id: str, manifest: dict[str, Any]) -> None:
        path = self.settings.artifacts_path / f"{record_id}.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
