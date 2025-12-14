# Semantic Video Search Engine

Search video content with natural language using **CLIP embeddings** + **FAISS vector database**.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│    CLIP     │
│  Frontend   │     │   Backend   │     │   Model     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │    FAISS    │
                    │    Index    │
                    └─────────────┘
```

**Pipeline:**
1. **Ingest** → Upload MP4 video
2. **Extract** → OpenCV pulls 1 frame/second  
3. **Embed** → CLIP converts frames to 512-dim vectors
4. **Index** → FAISS stores vectors for fast similarity search
5. **Search** → Text query → CLIP embedding → cosine similarity → top results

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python server.py
# API runs at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# UI runs at http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload video file |
| POST | `/index?filename=X&fps=1` | Index video |
| GET | `/search?query=X&top_k=5` | Search with text |
| GET | `/frame/{index}` | Get frame image |
| GET | `/health` | Health check |

## Usage Example

```python
from video_search import VideoSearchEngine

engine = VideoSearchEngine()

# Index a video
engine.build_index("traffic.mp4", fps=1)
engine.save("my_index")

# Search
results = engine.search("red car driving fast", top_k=5)
for r in results:
    print(f"{r['timestamp_sec']:.1f}s - score: {r['score']:.2f}")
```

## Tech Stack

- **Model**: CLIP (clip-ViT-B-32) via sentence-transformers
- **Vector DB**: FAISS (IndexFlatIP with L2 normalization)
- **Backend**: FastAPI + Python
- **Frontend**: Next.js + Tailwind
- **Frame Extraction**: OpenCV


