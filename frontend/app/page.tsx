"use client";

import { useState, useRef, useCallback } from "react";

interface SearchResult {
  rank: number;
  score: number;
  timestamp_sec: number;
  timestamp_ms: number;
  frame_path: string;
  frame_index: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VideoSearchApp() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [indexing, setIndexing] = useState(false);
  const [indexed, setIndexed] = useState(false);
  const [status, setStatus] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);

  const uploadAndIndex = async () => {
    if (!videoFile) return;
    
    setIndexing(true);
    setStatus("Uploading video...");
    
    try {
      // Upload
      const formData = new FormData();
      formData.append("file", videoFile);
      
      const uploadRes = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      
      if (!uploadRes.ok) throw new Error("Upload failed");
      const uploadData = await uploadRes.json();
      
      // Index
      setStatus("Indexing video (extracting frames & creating embeddings)...");
      const indexRes = await fetch(
        `${API_URL}/index?filename=${encodeURIComponent(uploadData.filename)}&fps=1`,
        { method: "POST" }
      );
      
      if (!indexRes.ok) throw new Error("Indexing failed");
      const indexData = await indexRes.json();
      
      setStatus(`Indexed ${indexData.frames} frames`);
      setIndexed(true);
      setVideoUrl(URL.createObjectURL(videoFile));
    } catch (err) {
      setStatus(`Error: ${err}`);
    } finally {
      setIndexing(false);
    }
  };

  const search = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/search?query=${encodeURIComponent(query)}&top_k=5`
      );
      
      if (!res.ok) throw new Error("Search failed");
      const data = await res.json();
      setResults(data.results);
    } catch (err) {
      setStatus(`Search error: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const seekTo = useCallback((timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp;
      videoRef.current.play();
    }
  }, []);

  const formatTime = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Semantic Video Search</h1>
        <p className="text-gray-400 mb-8">
          Search video content with natural language using CLIP embeddings
        </p>

        {/* Upload Section */}
        {!indexed && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl mb-4">1. Upload & Index Video</h2>
            <div className="flex gap-4 items-center">
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                className="flex-1 bg-gray-700 rounded px-4 py-2"
              />
              <button
                onClick={uploadAndIndex}
                disabled={!videoFile || indexing}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-2 rounded font-medium"
              >
                {indexing ? "Processing..." : "Upload & Index"}
              </button>
            </div>
            {status && <p className="mt-4 text-gray-300">{status}</p>}
          </div>
        )}

        {/* Search Section */}
        {indexed && (
          <>
            <div className="bg-gray-800 rounded-lg p-6 mb-8">
              <h2 className="text-xl mb-4">2. Search Video</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && search()}
                  placeholder='Try: "person walking", "red car", "outdoor scene"'
                  className="flex-1 bg-gray-700 rounded px-4 py-3 text-lg"
                />
                <button
                  onClick={search}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-8 py-3 rounded font-medium"
                >
                  {loading ? "Searching..." : "Search"}
                </button>
              </div>
            </div>

            {/* Video Player */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-lg mb-3">Video Player</h3>
                <video
                  ref={videoRef}
                  src={videoUrl}
                  controls
                  className="w-full rounded-lg bg-black"
                />
              </div>

              {/* Results */}
              <div>
                <h3 className="text-lg mb-3">
                  Search Results {results.length > 0 && `(${results.length})`}
                </h3>
                <div className="space-y-3">
                  {results.map((r) => (
                    <div
                      key={r.frame_index}
                      onClick={() => seekTo(r.timestamp_sec)}
                      className="bg-gray-800 rounded-lg p-4 cursor-pointer hover:bg-gray-700 transition flex items-center gap-4"
                    >
                      <img
                        src={`${API_URL}/frame/${r.frame_index}`}
                        alt={`Frame at ${r.timestamp_sec}s`}
                        className="w-32 h-20 object-cover rounded"
                      />
                      <div>
                        <div className="font-medium">
                          {formatTime(r.timestamp_sec)}
                        </div>
                        <div className="text-gray-400 text-sm">
                          Score: {(r.score * 100).toFixed(1)}%
                        </div>
                        <div className="text-blue-400 text-sm">
                          Click to jump →
                        </div>
                      </div>
                    </div>
                  ))}
                  {results.length === 0 && !loading && (
                    <p className="text-gray-500">
                      Enter a search query to find moments in your video
                    </p>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Tech Stack */}
        <div className="mt-12 pt-8 border-t border-gray-700">
          <h3 className="text-lg mb-4">Tech Stack</h3>
          <div className="flex flex-wrap gap-3">
            {["CLIP (OpenAI)", "FAISS", "FastAPI", "Next.js", "OpenCV", "sentence-transformers"].map(
              (tech) => (
                <span
                  key={tech}
                  className="bg-gray-800 px-3 py-1 rounded text-sm"
                >
                  {tech}
                </span>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
