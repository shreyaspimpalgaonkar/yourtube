# Quick Start Guide

## Prerequisites

- Python 3.10+ installed
- Node.js 18+ and npm installed
- API keys:
  - `GRAPHON_API_KEY` for video understanding
  - Google API key (set via `google-genai` client) for Gemini/Veo

## Setup Steps

### 1. Set Environment Variables

```bash
export GRAPHON_API_KEY="your_graphon_api_key"
# Google API key is set automatically when using google-genai client
```

### 2. Start Backend Server

```bash
cd server
./start-backend.sh
```

Or manually:
```bash
cd server/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend will run on `http://localhost:8000`

### 3. Start Frontend Server (in a new terminal)

```bash
cd server
./start-frontend.sh
```

Or manually:
```bash
cd server/frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000`

## Usage Flow

1. **Upload Video**: Go to http://localhost:3000 and upload a video file
2. **Query Video**: Ingest and query the video with natural language
3. **Detect Cuts**: Automatically detect scene cuts
4. **Process Snippets**: Add branding logos to snippets
5. **Merge Video**: Combine all snippets into final video

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (needs 3.10+)
- Check if port 8000 is available
- Verify environment variables are set

### Frontend won't start
- Check Node.js version: `node --version` (needs 18+)
- Check if port 3000 is available
- Try deleting `node_modules` and running `npm install` again

### Video processing fails
- Ensure API keys are set correctly
- Check backend logs for detailed error messages
- Verify video file format is supported (MP4, MOV, AVI, MKV)

