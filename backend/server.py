"""
FastAPI Server for Semantic Video Search
Endpoints: /index (POST), /search (GET), /health (GET)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import shutil
from video_search import VideoSearchEngine

app = FastAPI(title="Semantic Video Search API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
engine = VideoSearchEngine()
VIDEO_DIR = "uploads"
FRAMES_DIR = "frames"
INDEX_PATH = "video_index"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class IndexRequest(BaseModel):
    fps: Optional[int] = 1


@app.get("/health")
def health():
    return {"status": "ok", "indexed": engine.index is not None}


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file"""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Invalid video format")
    
    path = os.path.join(VIDEO_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    return {"filename": file.filename, "path": path}


@app.post("/index")
async def index_video(filename: str, fps: int = 1):
    """Index a video file for search"""
    video_path = os.path.join(VIDEO_DIR, filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(404, f"Video not found: {filename}")
    
    try:
        engine.build_index(video_path, output_dir=FRAMES_DIR, fps=fps)
        engine.save(INDEX_PATH)
        return {
            "status": "indexed",
            "frames": len(engine.frame_data),
            "video": filename
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/search")
def search(query: str, top_k: int = 5):
    """Search indexed video with natural language"""
    if engine.index is None:
        # Try loading saved index
        try:
            engine.load(INDEX_PATH)
        except:
            raise HTTPException(400, "No video indexed. Upload and index a video first.")
    
    results = engine.search(query, top_k=top_k)
    return {
        "query": query,
        "results": results
    }


@app.get("/frame/{frame_index}")
def get_frame(frame_index: int):
    """Get a specific frame image"""
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame_index:05d}.jpg")
    if not os.path.exists(frame_path):
        raise HTTPException(404, "Frame not found")
    return FileResponse(frame_path, media_type="image/jpeg")


@app.get("/video/{filename}")
def get_video(filename: str):
    """Stream video file"""
    video_path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(404, "Video not found")
    return FileResponse(video_path, media_type="video/mp4")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
