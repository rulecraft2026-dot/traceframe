from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import Settings, get_settings
from .models import GenerationRequest, HealthResponse, ProvenanceRecord, ReplayRequest
from .pipeline import TraceFramePipeline
from .repository import ProvenanceRepository

settings = get_settings()
repository = ProvenanceRepository(settings.database_path)
pipeline = TraceFramePipeline(settings, repository)

app = FastAPI(
    title="TraceFrame API",
    version="1.0.0",
    description="Provenance-first AI media generation with Genblaze and Backblaze B2.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse)
def health(config: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        mode="live" if config.live_ready and not config.demo_mode else "demo",
        storage="backblaze-b2" if config.live_ready and not config.demo_mode else "local",
    )


@app.post("/api/generations", response_model=ProvenanceRecord, status_code=201)
def generate(request: GenerationRequest) -> ProvenanceRecord:
    return pipeline.generate(request)


@app.get("/api/generations", response_model=list[ProvenanceRecord])
def history(limit: int = Query(default=50, ge=1, le=200)) -> list[ProvenanceRecord]:
    return repository.list(limit)


@app.get("/api/generations/{record_id}", response_model=ProvenanceRecord)
def get_generation(record_id: str) -> ProvenanceRecord:
    record = repository.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found")
    return record


@app.post("/api/generations/{record_id}/replay", response_model=ProvenanceRecord, status_code=201)
def replay(record_id: str, request: ReplayRequest) -> ProvenanceRecord:
    parent = repository.get(record_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Generation not found")
    return pipeline.generate(
        GenerationRequest(prompt=request.prompt_override or parent.prompt, **parent.params),
        parent_id=parent.id,
    )


@app.get("/artifacts/{filename}")
def artifact(filename: str) -> FileResponse:
    path = (settings.artifacts_path / filename).resolve()
    root = settings.artifacts_path.resolve()
    if root not in path.parents or not path.exists() or path.suffix == ".json":
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path)


@app.get("/manifests/{record_id}.json")
def manifest(record_id: str) -> FileResponse:
    path = settings.artifacts_path / f"{record_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    return FileResponse(path, media_type="application/json")
