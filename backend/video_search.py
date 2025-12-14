"""
Semantic Video Search Engine using CLIP
Extracts frames, creates embeddings, stores in FAISS, enables text-to-video search
"""

import os
import cv2
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer, util
import faiss
import pickle
from pathlib import Path

class VideoSearchEngine:
    def __init__(self, model_name='clip-ViT-B-32'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.frame_data = []  # stores {timestamp, frame_path}
        self.embedding_dim = 512
        
    def extract_frames(self, video_path: str, output_dir: str, fps: int = 1) -> list:
        """Extract frames from video at specified FPS"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / fps)
        
        frames = []
        frame_count = 0
        saved_count = 0VS
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_path = os.path.join(output_dir, f"frame_{saved_count:05d}.jpg")
                cv2.imwrite(frame_path, frame)
                
                frames.append({
                    'timestamp_ms': timestamp_ms,
                    'timestamp_sec': timestamp_ms / 1000,
                    'frame_path': frame_path,
                    'frame_index': saved_count
                })
                saved_count += 1
                
            frame_count += 1
            
        cap.release()
        print(f"Extracted {len(frames)} frames from {video_path}")
        return frames
    
    def create_embeddings(self, frames: list) -> np.ndarray:
        """Create CLIP embeddings for extracted frames"""
        images = []
        for f in frames:
            img = Image.open(f['frame_path'])
            images.append(img)
        
        print(f"Creating embeddings for {len(images)} frames...")
        embeddings = self.model.encode(images, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.astype('float32')
    
    def build_index(self, video_path: str, output_dir: str = "frames", fps: int = 1):
        """Full pipeline: extract frames, embed, build FAISS index"""
        # Extract frames
        self.frame_data = self.extract_frames(video_path, output_dir, fps)
        
        # Create embeddings
        embeddings = self.create_embeddings(self.frame_data)
        
        # Build FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine sim
        faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
        self.index.add(embeddings)
        
        print(f"Built index with {self.index.ntotal} vectors")
        return self
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Search video frames using natural language query"""
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.frame_data):
                result = {
                    'rank': i + 1,
                    'score': float(score),
                    'timestamp_sec': self.frame_data[idx]['timestamp_sec'],
                    'timestamp_ms': self.frame_data[idx]['timestamp_ms'],
                    'frame_path': self.frame_data[idx]['frame_path'],
                    'frame_index': self.frame_data[idx]['frame_index']
                }
                results.append(result)
        
        return results
    
    def save(self, path: str):
        """Save index and frame data to disk"""
        data = {
            'frame_data': self.frame_data,
        }
        with open(f"{path}_metadata.pkl", 'wb') as f:
            pickle.dump(data, f)
        faiss.write_index(self.index, f"{path}_index.faiss")
        print(f"Saved index to {path}")
    
    def load(self, path: str):
        """Load index and frame data from disk"""
        with open(f"{path}_metadata.pkl", 'rb') as f:
            data = pickle.load(f)
        self.frame_data = data['frame_data']
        self.index = faiss.read_index(f"{path}_index.faiss")
        print(f"Loaded index with {self.index.ntotal} vectors")
        return self


# Demo usage
if __name__ == "__main__":
    engine = VideoSearchEngine()
    
