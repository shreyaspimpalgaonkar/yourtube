# Video Ads Processing Pipeline - Full Stack Application

A full-stack application for processing videos with AI: upload, query, detect cuts, add branding, and merge videos.

## Architecture

- **Backend**: FastAPI server (`server/backend/`)
- **Frontend**: Next.js React application (`server/frontend/`)

## Setup

### Backend Setup

1. Navigate to backend directory:
```bash
cd server/backend
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export GRAPHON_API_KEY="your_graphon_api_key"
export GOOGLE_API_KEY="your_google_api_key"  # For Gemini/Veo
```

5. Run the server:
```bash
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd server/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage Flow

1. **Upload Video**: Upload a video file through the web interface
2. **Query Video**: Ingest and query the video with natural language (requires Graphon API)
3. **Detect Cuts**: Automatically detect scene cuts and split into snippets
4. **Process Snippets**: Add branding logos to snippets using AI (Gemini + Veo)
5. **Merge Video**: Combine all processed snippets into final branded video

## API Endpoints

### Backend API (http://localhost:8000)

- `POST /api/upload` - Upload video file
- `POST /api/ingest` - Ingest video with Graphon
- `POST /api/query` - Query video with natural language
- `POST /api/detect-cuts` - Detect scene cuts
- `POST /api/process-snippet` - Process snippet(s) with branding
- `POST /api/merge` - Merge videos
- `GET /api/status/{job_id}` - Get job status
- `GET /api/snippets` - Get list of snippets
- `GET /api/video/{file_id}` - Get video file
- `GET /api/output/{filename}` - Get output video

## Environment Variables

Required environment variables:

- `GRAPHON_API_KEY`: API key for Graphon video understanding
- `GOOGLE_API_KEY`: API key for Google Gemini/Veo (set via google-genai client)

## Notes

- Video processing jobs run asynchronously in the background
- Check job status using the `/api/status/{job_id}` endpoint
- Large videos may take several minutes to process
- Ensure you have sufficient disk space for video outputs

