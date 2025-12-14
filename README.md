# 🎬 AI Video Ads Pipeline

An AI-powered video processing pipeline that automatically generates branded content using Google's Gemini and Veo models. The system analyzes video content, identifies key moments, and seamlessly integrates brand logos through AI-generated video interpolation.

## ✨ Features

- **🔍 Intelligent Video Analysis**: Uses Gemini to understand video content and identify optimal moments for brand placement
- **🎨 AI Logo Generation**: Generates brand logos using Gemini 3 Pro (Nano Banana)
- **🎥 Video Interpolation**: Leverages Veo 3.1 for smooth video transitions with brand integration
- **🎯 Character-Based Targeting**: Maps specific characters/scenes to different brands (e.g., Goku → Red Bull, Vegeta → Monster)
- **⚡ Parallel Processing**: Processes multiple video snippets concurrently for faster results
- **🖥️ Web Interface**: React-based frontend for video querying and visualization

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Video Input   │────▶│  Scene Analysis │────▶│  Logo Placement │
│    (MP4/etc)    │     │    (Gemini)     │     │    (Gemini 3)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Branded Video  │◀────│ Video Merging   │◀────│  Interpolation  │
│     Output      │     │   (MoviePy)     │     │    (Veo 3.1)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Google Cloud credentials with access to Gemini and Veo APIs

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/agi-hackathon.git
cd agi-hackathon

# Install dependencies with uv
uv sync

# Or with pip
pip install -r requirements.txt
```

### Environment Setup

Set up your Google AI credentials:

```bash
export GOOGLE_API_KEY="your-api-key-here"
# Or use Google Cloud authentication
gcloud auth application-default login
```

### Running the Pipeline

```bash
# Process a single video snippet
uv run process_goku_snippet.py 8

# Process all relevant snippets in parallel
uv run process_goku_snippet.py --all
```

## 📁 Project Structure

```
agi-hackathon/
├── process_goku_snippet.py  # Main processing pipeline
├── ingest_video.py          # Video ingestion utilities
├── query_video.py           # Video querying with Gemini
├── detect_cuts.py           # Scene cut detection
├── merge_branded_video.py   # Video merging utilities
├── models.py                # Data models and schemas
├── server/                  # Backend server components
├── video-ads-prototype/     # Next.js web frontend
│   ├── src/
│   │   ├── app/            # Next.js app router
│   │   │   └── api/        # API routes (Graphon, Veo)
│   │   └── components/     # React components
│   └── public/             # Static assets
├── documentation/          # API docs and references
└── logos/                  # Brand logo assets
```

## 🔧 Core Components

### Video Processing Pipeline (`process_goku_snippet.py`)

The main processing script that:
1. Generates brand logos using Gemini 3 Pro
2. Extracts key frames from video snippets
3. Adds logos to frames with proper positioning
4. Generates interpolated video using Veo 3.1
5. Preserves audio throughout the process

### Web Interface (`video-ads-prototype/`)

A Next.js application providing:
- Video upload and querying
- Ad placement visualization
- Real-time processing status

## 📚 API Reference

### Graphon API (Video Querying)

- `POST /api/graphon/upload` - Upload video for processing
- `POST /api/graphon/query` - Query video content
- `GET /api/graphon/status` - Check processing status
- `GET /api/graphon/cache` - Get cached results

### Veo API (Video Generation)

- `POST /api/veo/generate` - Generate interpolated video

## 🛠️ Development

### Running the Web Frontend

```bash
cd video-ads-prototype
npm install
npm run dev
```

Visit `http://localhost:3000` to access the web interface.

### Running Tests

```bash
python test_video_processing.py
python test_veo_interpolation.py
```

## 📝 Dependencies

Key dependencies include:
- `google-genai` - Google AI SDK for Gemini and Veo
- `moviepy` - Video editing and processing
- `opencv-python` - Computer vision utilities
- `pillow` - Image processing
- `rich` - Terminal UI and progress bars

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Google AI for Gemini and Veo APIs
- The MoviePy team for excellent video processing tools
- Built during an AGI Hackathon 🚀
