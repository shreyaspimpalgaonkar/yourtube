"""
FastAPI Backend Server for Video Processing Pipeline
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict
import uvicorn

# Add parent directory to path to import Python scripts
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic import BaseModel

app = FastAPI(title="Video Ads Processing API")


class IngestRequest(BaseModel):
    file_id: str


class DetectCutsRequest(BaseModel):
    file_id: str


class MergeRequest(BaseModel):
    output_name: Optional[str] = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "server_outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Job status tracking
job_status: Dict[str, Dict] = {}


class VideoUploadResponse(BaseModel):
    file_id: str
    filename: str
    message: str


class QueryRequest(BaseModel):
    query: str
    group_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    segments: List[Dict]
    group_id: str


class ProcessSnippetRequest(BaseModel):
    snippet_number: Optional[int] = None
    process_all: bool = False


class ProcessSnippetResponse(BaseModel):
    job_id: str
    message: str


@app.get("/")
async def root():
    return {"message": "Video Ads Processing API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing."""
    try:
        # Save uploaded file
        file_id = f"{Path(file.filename).stem}_{int(asyncio.get_event_loop().time())}"
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return VideoUploadResponse(
            file_id=file_id,
            filename=file.filename,
            message=f"Video uploaded successfully: {file.filename}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest")
async def ingest_video(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest video with Graphon API."""
    try:
        file_id = request.file_id
        
        # Find uploaded file
        files = list(UPLOAD_DIR.glob(f"{file_id}_*"))
        if not files:
            raise HTTPException(status_code=404, detail="File not found")
        
        video_file = files[0]
        job_id = f"ingest_{file_id}"
        
        # Start background task
        background_tasks.add_task(run_ingest, str(video_file), job_id)
        
        job_status[job_id] = {
            "status": "processing",
            "message": "Video ingestion started"
        }
        
        return {"job_id": job_id, "message": "Ingestion started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_ingest(video_path: str, job_id: str):
    """Run video ingestion in background."""
    try:
        import asyncio
        from graphon_client import GraphonClient
        import os
        import json
        
        api_key = os.environ.get("GRAPHON_API_KEY")
        if not api_key:
            raise ValueError("GRAPHON_API_KEY not set")
        
        client = GraphonClient(api_key=api_key)
        
        def on_progress(step, current, total):
            job_status[job_id]["message"] = f"{step}: {current}/{total}"
        
        group_id = await client.upload_process_and_create_group(
            file_paths=[video_path],
            group_name="Video Processing",
            on_progress=on_progress
        )
        
        # Save to cache
        cache_file = BASE_DIR / ".graphon_cache.json"
        with open(cache_file, "w") as f:
            json.dump({
                "file_name": Path(video_path).name,
                "group_id": group_id,
                "group_name": "Video Processing",
            }, f, indent=2)
        
        job_status[job_id] = {
            "status": "completed",
            "message": "Video ingestion completed",
            "group_id": group_id
        }
    except Exception as e:
        import traceback
        job_status[job_id] = {
            "status": "failed",
            "message": f"Ingestion failed: {str(e)}",
            "error": traceback.format_exc()
        }


@app.post("/api/query", response_model=QueryResponse)
async def query_video(request: QueryRequest):
    """Query video with natural language."""
    try:
        # Load cache to get group_id
        cache_file = BASE_DIR / ".graphon_cache.json"
        if not cache_file.exists():
            raise HTTPException(status_code=404, detail="No processed video found. Please ingest a video first.")
        
        with open(cache_file) as f:
            cache = json.load(f)
        
        group_id = request.group_id or cache.get("group_id")
        if not group_id:
            raise HTTPException(status_code=404, detail="No group_id found")
        
        # Import query logic
        from query_video import query
        from graphon_client import GraphonClient
        import os
        
        api_key = os.environ.get("GRAPHON_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="GRAPHON_API_KEY not set")
        
        client = GraphonClient(api_key=api_key)
        response = await query(client, group_id, request.query)
        
        # Extract video segments
        video_sources = [s for s in response.sources if s.get("node_type") == "video"]
        segments = [
            {
                "start_time": s.get("start_time", 0),
                "end_time": s.get("end_time", 0),
                "start_time_formatted": format_time(s.get("start_time", 0)),
                "end_time_formatted": format_time(s.get("end_time", 0)),
            }
            for s in video_sources
        ]
        
        return QueryResponse(
            answer=response.answer,
            segments=segments,
            group_id=group_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_time(seconds):
    """Format seconds as MM:SS."""
    if seconds is None:
        return "??:??"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


@app.post("/api/detect-cuts")
async def detect_cuts(request: DetectCutsRequest, background_tasks: BackgroundTasks):
    """Detect scene cuts in video."""
    try:
        file_id = request.file_id
        
        files = list(UPLOAD_DIR.glob(f"{file_id}_*"))
        if not files:
            raise HTTPException(status_code=404, detail="File not found")
        
        video_file = files[0]
        job_id = f"cuts_{file_id}"
        
        background_tasks.add_task(run_detect_cuts, str(video_file), job_id)
        
        job_status[job_id] = {
            "status": "processing",
            "message": "Cut detection started"
        }
        
        return {"job_id": job_id, "message": "Cut detection started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_detect_cuts(video_path: str, job_id: str):
    """Run cut detection in background."""
    try:
        import detect_cuts
        original_video_file = detect_cuts.VIDEO_FILE
        detect_cuts.VIDEO_FILE = video_path
        
        from detect_cuts import main as detect_main
        detect_main()
        
        detect_cuts.VIDEO_FILE = original_video_file
        
        # Load snippets info
        snippets_file = BASE_DIR / "snippets" / "snippets_info.json"
        snippets_info = []
        if snippets_file.exists():
            with open(snippets_file) as f:
                snippets_info = json.load(f)
        
        job_status[job_id] = {
            "status": "completed",
            "message": f"Found {len(snippets_info)} snippets",
            "snippets_count": len(snippets_info),
            "snippets": snippets_info
        }
    except Exception as e:
        job_status[job_id] = {
            "status": "failed",
            "message": f"Cut detection failed: {str(e)}"
        }


@app.post("/api/process-snippet", response_model=ProcessSnippetResponse)
async def process_snippet(request: ProcessSnippetRequest, background_tasks: BackgroundTasks):
    """Process video snippet(s) with branding."""
    try:
        import time
        job_id = f"process_{int(time.time())}"
        
        background_tasks.add_task(
            run_process_snippet,
            request.snippet_number,
            request.process_all,
            job_id
        )
        
        job_status[job_id] = {
            "status": "processing",
            "message": "Snippet processing started"
        }
        
        return ProcessSnippetResponse(
            job_id=job_id,
            message="Processing started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_process_snippet(snippet_number: Optional[int], process_all: bool, job_id: str):
    """Run snippet processing in background."""
    try:
        from process_goku_snippet import main_async
        
        if process_all:
            await main_async(None)
        else:
            if snippet_number is None:
                raise ValueError("snippet_number required when process_all is False")
            await main_async(snippet_number)
        
        job_status[job_id] = {
            "status": "completed",
            "message": "Snippet processing completed"
        }
    except Exception as e:
        job_status[job_id] = {
            "status": "failed",
            "message": f"Processing failed: {str(e)}"
        }


@app.post("/api/merge")
async def merge_video(request: Optional[MergeRequest] = None, background_tasks: BackgroundTasks = None):
    """Merge processed snippets into final video."""
    try:
        import time
        output_name = None
        if request:
            output_name = request.output_name
        
        job_id = f"merge_{int(time.time())}"
        
        background_tasks.add_task(run_merge, output_name, job_id)
        
        job_status[job_id] = {
            "status": "processing",
            "message": "Video merging started"
        }
        
        return {"job_id": job_id, "message": "Merging started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_merge(output_name: Optional[str], job_id: str):
    """Run video merge in background."""
    try:
        from merge_branded_video import merge_all_snippets
        
        if output_name:
            output_path = OUTPUT_DIR / output_name
        else:
            output_path = OUTPUT_DIR / "branded_video.mp4"
        
        success = merge_all_snippets(output_path)
        
        if success:
            job_status[job_id] = {
                "status": "completed",
                "message": "Video merge completed",
                "output_path": str(output_path)
            }
        else:
            job_status[job_id] = {
                "status": "failed",
                "message": "Video merge failed"
            }
    except Exception as e:
        job_status[job_id] = {
            "status": "failed",
            "message": f"Merge failed: {str(e)}"
        }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get status of a background job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status[job_id]


@app.get("/api/snippets")
async def get_snippets():
    """Get list of available snippets."""
    snippets_file = BASE_DIR / "snippets" / "snippets_info.json"
    if not snippets_file.exists():
        return {"snippets": []}
    
    with open(snippets_file) as f:
        snippets = json.load(f)
    
    return {"snippets": snippets}


@app.get("/api/video/{file_id}")
async def get_video(file_id: str):
    """Get video file."""
    files = list(UPLOAD_DIR.glob(f"{file_id}_*"))
    if not files:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(files[0])


@app.get("/api/output/{filename}")
async def get_output(filename: str):
    """Get output video file."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

