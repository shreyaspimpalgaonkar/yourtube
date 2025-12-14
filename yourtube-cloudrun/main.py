"""
YourTube.dev - Video Ads Processing Pipeline Demo
Deployed on Google Cloud Run
"""
import os
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# GCS Base URL
GCS_BASE = "https://storage.googleapis.com/yourtube-dev-videos"

# Pipeline stages data
PIPELINE_STAGES = [
    {
        "id": 1,
        "title": "Original Video",
        "description": "Raw video content is uploaded and prepared for processing",
        "icon": "📤",
        "color": "from-blue-500 to-blue-600",
        "details": "The original Dragon Ball Z video is ingested into our system"
    },
    {
        "id": 2,
        "title": "Scene Detection",
        "description": "AI detects natural scene cuts and transitions",
        "icon": "✂️",
        "color": "from-purple-500 to-purple-600",
        "details": "PySceneDetect analyzes the video and splits it into 104 individual snippets based on scene changes"
    },
    {
        "id": 3,
        "title": "Character Query",
        "description": "Graphon API identifies characters and key moments",
        "icon": "🔍",
        "color": "from-indigo-500 to-indigo-600",
        "details": "Natural language queries find Goku and Vegeta scenes for targeted branding"
    },
    {
        "id": 4,
        "title": "Brand Frame Editing",
        "description": "AI edits first/last frames with sponsor logos",
        "icon": "🎨",
        "color": "from-pink-500 to-pink-600",
        "details": "Gemini 3.0 + Nano Banana seamlessly integrate brand logos into scene frames"
    },
    {
        "id": 5,
        "title": "Veo Interpolation",
        "description": "Google Veo generates smooth transitions",
        "icon": "🎬",
        "color": "from-amber-500 to-amber-600",
        "details": "Veo AI creates natural video interpolation between original and branded frames"
    },
    {
        "id": 6,
        "title": "Audio Sync & Trim",
        "description": "Original audio is preserved and synced",
        "icon": "🔊",
        "color": "from-green-500 to-green-600",
        "details": "FFmpeg extracts and reattaches original audio, trimming to match"
    },
    {
        "id": 7,
        "title": "Final Merge",
        "description": "All processed snippets merged into final video",
        "icon": "🔗",
        "color": "from-red-500 to-red-600",
        "details": "MoviePy concatenates all snippets maintaining perfect timing and transitions"
    }
]

# Example snippets with video URLs
PIPELINE_EXAMPLES = [
    {
        "name": "Goku Scene #8",
        "snippet_id": "0008",
        "frames": "119-162",
        "character": "Goku",
        "videos": {
            "original": f"{GCS_BASE}/snippets/0008_119_162.mp4",
            "interpolated": f"{GCS_BASE}/interpolated/video_119_162.mp4",
            "trimmed": f"{GCS_BASE}/trimmed/video_119_162_trimmed.mp4"
        }
    },
    {
        "name": "Goku Scene #11",
        "snippet_id": "0011",
        "frames": "183-279",
        "character": "Goku",
        "videos": {
            "original": f"{GCS_BASE}/snippets/0011_183_279.mp4",
            "interpolated": f"{GCS_BASE}/interpolated/video_183_279.mp4",
            "trimmed": f"{GCS_BASE}/trimmed/video_183_279_trimmed.mp4"
        }
    },
    {
        "name": "Vegeta Scene #18",
        "snippet_id": "0018",
        "frames": "618-789",
        "character": "Vegeta",
        "videos": {
            "original": f"{GCS_BASE}/snippets/0018_618_789.mp4",
            "interpolated": f"{GCS_BASE}/interpolated/video_618_789.mp4",
            "trimmed": f"{GCS_BASE}/trimmed/video_618_789_trimmed.mp4"
        }
    }
]

DEMO_QUERY_RESPONSES = {
    "goku": {
        "answer": "Goku appears in multiple scenes throughout the video. He is shown in intense battle sequences at timestamps 119-162, 183-279, 426-617, 1230-1365, and 1783-1934.",
        "segments": [
            {"start_time": 119, "end_time": 162, "start_time_formatted": "1:59", "end_time_formatted": "2:42"},
            {"start_time": 183, "end_time": 279, "start_time_formatted": "3:03", "end_time_formatted": "4:39"},
            {"start_time": 426, "end_time": 617, "start_time_formatted": "7:06", "end_time_formatted": "10:17"},
        ]
    },
    "vegeta": {
        "answer": "Vegeta appears in key battle scenes at timestamps 618-789 and 1122-1229.",
        "segments": [
            {"start_time": 618, "end_time": 789, "start_time_formatted": "10:18", "end_time_formatted": "13:09"},
            {"start_time": 1122, "end_time": 1229, "start_time_formatted": "18:42", "end_time_formatted": "20:29"},
        ]
    },
    "default": {
        "answer": "This video showcases epic battles from Dragon Ball featuring Goku and Vegeta.",
        "segments": []
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YourTube.dev - AI Video Processing Pipeline</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'] },
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); }
        .glass-dark { background: rgba(0,0,0,0.3); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .float { animation: float 3s ease-in-out infinite; }
        @keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); } 50% { box-shadow: 0 0 40px rgba(99, 102, 241, 0.6); } }
        .pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }
        @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .animate-gradient { background-size: 200% 200%; animation: gradient 3s ease infinite; }
        .nav-item { position: relative; }
        .nav-item::after { content: ''; position: absolute; bottom: -2px; left: 50%; width: 0; height: 2px; background: linear-gradient(90deg, #6366f1, #a855f7); transition: all 0.3s; transform: translateX(-50%); }
        .nav-item:hover::after, .nav-item.active::after { width: 100%; }
        .video-container { position: relative; border-radius: 12px; overflow: hidden; }
        .video-container video { width: 100%; display: block; }
        .stage-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .stage-card:hover { transform: translateY(-4px) scale(1.02); }
        .timeline-line { background: linear-gradient(180deg, #6366f1 0%, #a855f7 50%, #ec4899 100%); }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #1f2937; }
        ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #6b7280; }
    </style>
</head>
<body class="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white">
    <!-- Animated Background -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"></div>
        <div class="absolute top-1/2 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-40 right-1/3 w-80 h-80 bg-pink-500/20 rounded-full blur-3xl"></div>
    </div>

    <!-- Navigation -->
    <nav class="glass-dark sticky top-0 z-50 border-b border-white/10">
        <div class="max-w-7xl mx-auto px-6">
            <div class="flex items-center justify-between h-20">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-2xl pulse-glow">
                        🎬
                    </div>
                    <div>
                        <span class="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">YourTube.dev</span>
                        <p class="text-xs text-gray-500">AI Video Processing</p>
                    </div>
                </div>
                <div class="flex items-center gap-1 bg-gray-800/50 rounded-full p-1">
                    <button onclick="showTab('home')" id="nav-home" class="nav-item active px-6 py-2.5 rounded-full font-medium transition-all bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                        🏠 Home
                    </button>
                    <button onclick="showTab('pipeline')" id="nav-pipeline" class="nav-item px-6 py-2.5 rounded-full font-medium transition-all text-gray-400 hover:text-white">
                        ⚡ Pipeline
                    </button>
                    <button onclick="showTab('sponsored')" id="nav-sponsored" class="nav-item px-6 py-2.5 rounded-full font-medium transition-all text-gray-400 hover:text-white">
                        💎 Sponsored
                    </button>
                </div>
                <div class="flex items-center gap-3">
                    <div class="flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/20 border border-green-500/30">
                        <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                        <span class="text-green-400 text-sm font-medium">Live</span>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <!-- Home Tab -->
    <div id="content-home">
        <div class="max-w-7xl mx-auto px-6 py-12">
            <div class="grid lg:grid-cols-3 gap-8">
                <!-- Main Video -->
                <div class="lg:col-span-2">
                    <div class="glass rounded-3xl overflow-hidden">
                        <div class="video-container">
                            <video id="main-video" class="w-full aspect-video bg-black" controls>
                                <source src="https://storage.googleapis.com/yourtube-dev-videos/branded_video.mp4" type="video/mp4">
                            </video>
                        </div>
                        <div class="p-6">
                            <div class="flex items-start justify-between mb-4">
                                <div>
                                    <h1 class="text-2xl font-bold mb-2">🔥 Dragon Ball Z - Goku vs Vegeta</h1>
                                    <p class="text-gray-400 text-sm">AI-Enhanced with Dynamic Brand Integration</p>
                                </div>
                                <div class="flex gap-2">
                                    <span class="px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-medium">AI Processed</span>
                                </div>
                            </div>
                            <div class="flex items-center gap-6 text-sm text-gray-500 mb-4">
                                <span class="flex items-center gap-1">👁️ 1.2M views</span>
                                <span class="flex items-center gap-1">📅 Just now</span>
                                <span class="flex items-center gap-1 text-amber-400">✨ Veo Enhanced</span>
                            </div>
                            <p class="text-gray-300 text-sm leading-relaxed">
                                This video demonstrates our complete AI pipeline: scene detection, character identification, 
                                dynamic brand integration using Nano Banana, and seamless interpolation via Google Veo.
                            </p>
                            <div class="flex flex-wrap gap-2 mt-4">
                                <span class="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs">Graphon API</span>
                                <span class="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs">Google Veo</span>
                                <span class="px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20 text-green-300 text-xs">Gemini 3.0</span>
                                <span class="px-3 py-1.5 rounded-lg bg-pink-500/10 border border-pink-500/20 text-pink-300 text-xs">Nano Banana 3</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sidebar -->
                <div class="space-y-6">
                    <div class="glass rounded-2xl p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span class="text-xl">⚡</span> Quick Stats
                        </h3>
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Snippets Processed</span>
                                <span class="font-bold text-indigo-400">104</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Scenes Branded</span>
                                <span class="font-bold text-purple-400">12</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Veo Generations</span>
                                <span class="font-bold text-pink-400">24</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Processing Time</span>
                                <span class="font-bold text-amber-400">~8 min</span>
                            </div>
                        </div>
                    </div>

                    <div class="glass rounded-2xl p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span class="text-xl">🎯</span> Characters Detected
                        </h3>
                        <div class="space-y-3">
                            <div class="flex items-center gap-3 p-3 rounded-xl bg-orange-500/10 border border-orange-500/20">
                                <span class="text-2xl">🟠</span>
                                <div>
                                    <p class="font-medium">Goku</p>
                                    <p class="text-xs text-gray-400">8 scenes detected</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-3 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                                <span class="text-2xl">🔵</span>
                                <div>
                                    <p class="font-medium">Vegeta</p>
                                    <p class="text-xs text-gray-400">4 scenes detected</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <button onclick="showTab('pipeline')" class="w-full py-4 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 font-semibold hover:from-indigo-400 hover:to-purple-400 transition-all transform hover:scale-[1.02] active:scale-[0.98]">
                        View Full Pipeline →
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Pipeline Tab -->
    <div id="content-pipeline" class="hidden">
        <div class="max-w-7xl mx-auto px-6 py-12">
            <!-- Header -->
            <div class="text-center mb-16">
                <h1 class="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                    AI Video Processing Pipeline
                </h1>
                <p class="text-gray-400 text-lg max-w-2xl mx-auto">
                    See exactly how we transform raw video into seamlessly branded content using cutting-edge AI
                </p>
            </div>

            <!-- Pipeline Stages -->
            <div class="relative mb-20">
                <div class="grid md:grid-cols-7 gap-4">
                    ${PIPELINE_STAGES_HTML}
                </div>
            </div>

            <!-- Example Processing -->
            <div class="mb-16">
                <h2 class="text-2xl font-bold mb-8 text-center">🎬 Live Processing Examples</h2>
                <div class="grid lg:grid-cols-3 gap-8">
                    ${PIPELINE_EXAMPLES_HTML}
                </div>
            </div>

            <!-- Video Comparison -->
            <div class="glass rounded-3xl p-8 mb-16">
                <h2 class="text-2xl font-bold mb-6 text-center">🔄 Before & After Comparison</h2>
                <div class="grid md:grid-cols-2 gap-8">
                    <div>
                        <h3 class="text-lg font-semibold mb-4 text-center text-gray-400">Original Snippet</h3>
                        <div class="video-container rounded-2xl overflow-hidden">
                            <video controls class="w-full">
                                <source src="https://storage.googleapis.com/yourtube-dev-videos/snippets/0008_119_162.mp4" type="video/mp4">
                            </video>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold mb-4 text-center text-indigo-400">After Veo Interpolation</h3>
                        <div class="video-container rounded-2xl overflow-hidden ring-2 ring-indigo-500/50">
                            <video controls class="w-full">
                                <source src="https://storage.googleapis.com/yourtube-dev-videos/trimmed/video_119_162_trimmed.mp4" type="video/mp4">
                            </video>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tech Stack -->
            <div class="glass rounded-3xl p-8">
                <h2 class="text-2xl font-bold mb-8 text-center">🛠️ Technology Stack</h2>
                <div class="grid md:grid-cols-4 gap-6">
                    <div class="text-center p-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20">
                        <div class="text-4xl mb-3">🔍</div>
                        <h3 class="font-bold mb-2">Graphon API</h3>
                        <p class="text-sm text-gray-400">Video understanding & natural language queries</p>
                    </div>
                    <div class="text-center p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20">
                        <div class="text-4xl mb-3">🎬</div>
                        <h3 class="font-bold mb-2">Google Veo</h3>
                        <p class="text-sm text-gray-400">AI video interpolation & generation</p>
                    </div>
                    <div class="text-center p-6 rounded-2xl bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20">
                        <div class="text-4xl mb-3">🧠</div>
                        <h3 class="font-bold mb-2">Gemini 3.0 + Nano Banana</h3>
                        <p class="text-sm text-gray-400">Intelligent frame editing & brand integration</p>
                    </div>
                    <div class="text-center p-6 rounded-2xl bg-gradient-to-br from-amber-500/10 to-amber-600/5 border border-amber-500/20">
                        <div class="text-4xl mb-3">🎞️</div>
                        <h3 class="font-bold mb-2">FFmpeg + MoviePy</h3>
                        <p class="text-sm text-gray-400">Video processing & audio synchronization</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Sponsored Tab -->
    <div id="content-sponsored" class="hidden">
        <div class="max-w-7xl mx-auto px-6 py-12">
            <div class="text-center mb-12">
                <h1 class="text-4xl font-bold mb-4 bg-gradient-to-r from-amber-400 via-orange-400 to-red-400 bg-clip-text text-transparent">
                    💎 Sponsored Content Gallery
                </h1>
                <p class="text-gray-400 text-lg">AI-generated branded videos with seamless sponsor integration</p>
            </div>

            <!-- Brand Logos Section -->
            <div class="glass rounded-3xl p-8 mb-12">
                <h2 class="text-2xl font-bold mb-6 text-center">🏷️ Brand Partners</h2>
                <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div class="bg-white/5 rounded-2xl p-6 text-center hover:bg-white/10 transition-all">
                        <img src="https://storage.googleapis.com/yourtube-dev-videos/logos/redbull_logo.png" alt="RedBull" class="h-24 mx-auto mb-4 object-contain">
                        <h3 class="font-semibold text-red-400">Red Bull</h3>
                        <p class="text-xs text-gray-500 mt-1">Energy Sponsor</p>
                    </div>
                    <div class="bg-white/5 rounded-2xl p-6 text-center hover:bg-white/10 transition-all">
                        <img src="https://storage.googleapis.com/yourtube-dev-videos/logos/monster_logo.png" alt="Monster" class="h-24 mx-auto mb-4 object-contain">
                        <h3 class="font-semibold text-green-400">Monster Energy</h3>
                        <p class="text-xs text-gray-500 mt-1">Gaming Partner</p>
                    </div>
                    <div class="bg-white/5 rounded-2xl p-6 text-center hover:bg-white/10 transition-all">
                        <img src="https://storage.googleapis.com/yourtube-dev-videos/branded_frames/athlead_logo.png" alt="Athlead" class="h-24 mx-auto mb-4 object-contain">
                        <h3 class="font-semibold text-blue-400">Athlead</h3>
                        <p class="text-xs text-gray-500 mt-1">Sports Tech</p>
                    </div>
                    <div class="bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-2xl p-6 text-center border border-amber-500/30">
                        <div class="h-24 flex items-center justify-center text-5xl">🏆</div>
                        <h3 class="font-semibold text-amber-400">Your Brand</h3>
                        <p class="text-xs text-gray-500 mt-1">Partner with us!</p>
                    </div>
                </div>
            </div>

            <!-- The Office Examples -->
            <div class="glass rounded-3xl p-8 mb-12">
                <h2 class="text-2xl font-bold mb-2 text-center">📺 The Office - Brand Integration Demo</h2>
                <p class="text-gray-400 text-center mb-8">AI seamlessly adds Red Bull branding to Michael Scott scenes</p>
                <div class="grid md:grid-cols-2 gap-8">
                    <div class="relative group">
                        <img src="https://storage.googleapis.com/yourtube-dev-videos/edited_frames/michael_with_redbull_1_24.png" alt="Michael with RedBull 1" class="w-full rounded-2xl">
                        <div class="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-red-500/90 text-white text-xs font-bold flex items-center gap-2">
                            <span>🎯</span> AI Edited
                        </div>
                        <div class="absolute bottom-4 left-4 right-4 glass rounded-xl p-3 opacity-0 group-hover:opacity-100 transition-all">
                            <p class="text-sm">Frame 24 - RedBull placement on Michael's desk</p>
                        </div>
                    </div>
                    <div class="relative group">
                        <img src="https://storage.googleapis.com/yourtube-dev-videos/edited_frames/michael_with_redbull_1_26.png" alt="Michael with RedBull 2" class="w-full rounded-2xl">
                        <div class="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-red-500/90 text-white text-xs font-bold flex items-center gap-2">
                            <span>🎯</span> AI Edited
                        </div>
                        <div class="absolute bottom-4 left-4 right-4 glass rounded-xl p-3 opacity-0 group-hover:opacity-100 transition-all">
                            <p class="text-sm">Frame 26 - Natural brand integration</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Frame Comparison: Original vs Branded -->
            <div class="glass rounded-3xl p-8 mb-12">
                <h2 class="text-2xl font-bold mb-2 text-center">🔄 Before & After: Frame Editing</h2>
                <p class="text-gray-400 text-center mb-8">Gemini 3.0 + Nano Banana seamlessly integrate logos into video frames</p>
                
                <div class="grid lg:grid-cols-2 gap-8 mb-8">
                    <!-- Athlead Example -->
                    <div class="space-y-4">
                        <h3 class="text-lg font-semibold text-center text-blue-400">Athlead Integration</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/branded_frames/original_first_frame.png" alt="Original First Frame" class="w-full rounded-xl">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-gray-800/80 text-xs">Original</div>
                            </div>
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/branded_frames/edited_first_frame.png" alt="Edited First Frame" class="w-full rounded-xl ring-2 ring-blue-500/50">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-blue-500/80 text-xs">+ Logo</div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/branded_frames/original_last_frame.png" alt="Original Last Frame" class="w-full rounded-xl">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-gray-800/80 text-xs">Original</div>
                            </div>
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/branded_frames/edited_last_frame.png" alt="Edited Last Frame" class="w-full rounded-xl ring-2 ring-blue-500/50">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-blue-500/80 text-xs">+ Logo</div>
                            </div>
                        </div>
                    </div>

                    <!-- Dragon Ball Examples -->
                    <div class="space-y-4">
                        <h3 class="text-lg font-semibold text-center text-orange-400">Dragon Ball Z - Goku Scene</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0008_0119_original.png" alt="Goku Original 119" class="w-full rounded-xl">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-gray-800/80 text-xs">Frame 119</div>
                            </div>
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0008_0119_processed.png" alt="Goku Processed 119" class="w-full rounded-xl ring-2 ring-orange-500/50">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-orange-500/80 text-xs">+ Sponsor</div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0008_0162_original.png" alt="Goku Original 162" class="w-full rounded-xl">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-gray-800/80 text-xs">Frame 162</div>
                            </div>
                            <div class="relative">
                                <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0008_0162_processed.png" alt="Goku Processed 162" class="w-full rounded-xl ring-2 ring-orange-500/50">
                                <div class="absolute top-2 left-2 px-2 py-1 rounded bg-orange-500/80 text-xs">+ Sponsor</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Vegeta Example -->
                <div class="mt-8">
                    <h3 class="text-lg font-semibold text-center text-blue-400 mb-4">Dragon Ball Z - Vegeta Scene</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="relative">
                            <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0018_0618_original.png" alt="Vegeta Original 618" class="w-full rounded-xl">
                            <div class="absolute top-2 left-2 px-2 py-1 rounded bg-gray-800/80 text-xs">Frame 618</div>
                        </div>
                        <div class="relative">
                            <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0018_0618_processed.png" alt="Vegeta Processed 618" class="w-full rounded-xl ring-2 ring-blue-500/50">
                            <div class="absolute top-2 left-2 px-2 py-1 rounded bg-blue-500/80 text-xs">+ Sponsor</div>
                        </div>
                        <div class="relative">
                            <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0018_0789_original.png" alt="Vegeta Original 789" class="w-full rounded-xl">
                            <div class="absolute top-2 left-2 px-2 py-1 rounded bg-gray-800/80 text-xs">Frame 789</div>
                        </div>
                        <div class="relative">
                            <img src="https://storage.googleapis.com/yourtube-dev-videos/proc_frames/0018_0789_processed.png" alt="Vegeta Processed 789" class="w-full rounded-xl ring-2 ring-blue-500/50">
                            <div class="absolute top-2 left-2 px-2 py-1 rounded bg-blue-500/80 text-xs">+ Sponsor</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Sponsored Videos -->
            <div class="mb-12">
                <h2 class="text-2xl font-bold mb-8 text-center">🎬 Sponsored Video Clips</h2>
                <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    <div class="glass rounded-2xl overflow-hidden group cursor-pointer transform transition-all hover:scale-[1.02]">
                        <div class="relative aspect-video">
                            <video class="w-full h-full object-cover" muted loop onmouseover="this.play()" onmouseout="this.pause()">
                                <source src="https://storage.googleapis.com/yourtube-dev-videos/trimmed/video_119_162_trimmed.mp4" type="video/mp4">
                            </video>
                            <div class="absolute top-3 left-3 px-2 py-1 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-xs font-bold">SPONSORED</div>
                        </div>
                        <div class="p-5">
                            <h3 class="font-semibold mb-2">Goku Power-Up</h3>
                            <p class="text-sm text-gray-400 mb-3">Frames 119-162 with brand integration</p>
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs">Monster</span>
                                <span class="text-xs text-gray-500">845K views</span>
                            </div>
                        </div>
                    </div>

                    <div class="glass rounded-2xl overflow-hidden group cursor-pointer transform transition-all hover:scale-[1.02]">
                        <div class="relative aspect-video">
                            <video class="w-full h-full object-cover" muted loop onmouseover="this.play()" onmouseout="this.pause()">
                                <source src="https://storage.googleapis.com/yourtube-dev-videos/trimmed/video_183_279_trimmed.mp4" type="video/mp4">
                            </video>
                            <div class="absolute top-3 left-3 px-2 py-1 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-xs font-bold">SPONSORED</div>
                        </div>
                        <div class="p-5">
                            <h3 class="font-semibold mb-2">Battle Sequence</h3>
                            <p class="text-sm text-gray-400 mb-3">Frames 183-279 with energy branding</p>
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs">Red Bull</span>
                                <span class="text-xs text-gray-500">1.1M views</span>
                            </div>
                        </div>
                    </div>

                    <div class="glass rounded-2xl overflow-hidden group cursor-pointer transform transition-all hover:scale-[1.02]">
                        <div class="relative aspect-video">
                            <video class="w-full h-full object-cover" muted loop onmouseover="this.play()" onmouseout="this.pause()">
                                <source src="https://storage.googleapis.com/yourtube-dev-videos/trimmed/video_618_789_trimmed.mp4" type="video/mp4">
                            </video>
                            <div class="absolute top-3 left-3 px-2 py-1 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-xs font-bold">SPONSORED</div>
                        </div>
                        <div class="p-5">
                            <h3 class="font-semibold mb-2">Vegeta Pride</h3>
                            <p class="text-sm text-gray-400 mb-3">Frames 618-789 with tech branding</p>
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs">Athlead</span>
                                <span class="text-xs text-gray-500">623K views</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Final Video -->
            <div class="glass rounded-3xl p-8">
                <h2 class="text-2xl font-bold mb-6 text-center">🏆 Final Branded Video</h2>
                <div class="max-w-4xl mx-auto">
                    <div class="video-container rounded-2xl overflow-hidden ring-2 ring-amber-500/30">
                        <video controls class="w-full">
                            <source src="https://storage.googleapis.com/yourtube-dev-videos/branded_video.mp4" type="video/mp4">
                        </video>
                    </div>
                    <p class="text-center text-gray-400 mt-4">Complete video with all sponsored segments seamlessly integrated</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="glass-dark border-t border-white/10 py-12 mt-20">
        <div class="max-w-7xl mx-auto px-6">
            <div class="flex flex-col md:flex-row items-center justify-between gap-6">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xl">🎬</div>
                    <span class="text-lg font-bold">YourTube.dev</span>
                </div>
                <p class="text-gray-500 text-sm">© 2024 YourTube.dev • AI-Powered Video Processing Pipeline</p>
                <div class="flex items-center gap-4 text-sm text-gray-400">
                    <span>Flask</span>
                    <span>•</span>
                    <span>Google Veo</span>
                    <span>•</span>
                    <span>Cloud Run</span>
                </div>
            </div>
        </div>
    </footer>

    <script>
        function showTab(tab) {
            ['home', 'pipeline', 'sponsored'].forEach(t => {
                document.getElementById('content-' + t).classList.add('hidden');
                const navBtn = document.getElementById('nav-' + t);
                navBtn.classList.remove('bg-gradient-to-r', 'from-indigo-500', 'to-purple-500', 'text-white', 'active');
                navBtn.classList.add('text-gray-400');
            });
            document.getElementById('content-' + tab).classList.remove('hidden');
            const activeBtn = document.getElementById('nav-' + tab);
            activeBtn.classList.add('bg-gradient-to-r', 'from-indigo-500', 'to-purple-500', 'text-white', 'active');
            activeBtn.classList.remove('text-gray-400');
        }
    </script>
</body>
</html>
"""

# Generate pipeline stages HTML
def generate_pipeline_html():
    stages_html = ""
    for stage in PIPELINE_STAGES:
        stages_html += f'''
        <div class="stage-card glass rounded-2xl p-4 text-center cursor-pointer hover:ring-2 hover:ring-indigo-500/50">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br {stage["color"]} flex items-center justify-center mx-auto mb-3 text-xl">
                {stage["icon"]}
            </div>
            <h3 class="font-semibold text-sm mb-1">{stage["title"]}</h3>
            <p class="text-xs text-gray-500 leading-tight">{stage["description"]}</p>
        </div>
        '''
    return stages_html

def generate_examples_html():
    examples_html = ""
    for ex in PIPELINE_EXAMPLES:
        char_color = "orange" if ex["character"] == "Goku" else "blue"
        examples_html += f'''
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-4 border-b border-white/10">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">{"🟠" if ex["character"] == "Goku" else "🔵"}</span>
                    <div>
                        <h3 class="font-semibold">{ex["name"]}</h3>
                        <p class="text-xs text-gray-400">Frames {ex["frames"]}</p>
                    </div>
                </div>
            </div>
            <div class="p-4 space-y-4">
                <div>
                    <p class="text-xs text-gray-500 mb-2">Original</p>
                    <video controls class="w-full rounded-lg">
                        <source src="{ex["videos"]["original"]}" type="video/mp4">
                    </video>
                </div>
                <div>
                    <p class="text-xs text-gray-500 mb-2">Veo Interpolated</p>
                    <video controls class="w-full rounded-lg">
                        <source src="{ex["videos"]["interpolated"]}" type="video/mp4">
                    </video>
                </div>
                <div>
                    <p class="text-xs text-gray-500 mb-2">Final (Trimmed + Audio)</p>
                    <video controls class="w-full rounded-lg ring-1 ring-{char_color}-500/30">
                        <source src="{ex["videos"]["trimmed"]}" type="video/mp4">
                    </video>
                </div>
            </div>
        </div>
        '''
    return examples_html

# Replace placeholders in template
FINAL_HTML = HTML_TEMPLATE.replace("${PIPELINE_STAGES_HTML}", generate_pipeline_html())
FINAL_HTML = FINAL_HTML.replace("${PIPELINE_EXAMPLES_HTML}", generate_examples_html())

@app.route("/")
def home():
    return render_template_string(FINAL_HTML)

@app.route("/health")
@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "yourtube.dev", "version": "2.0.0"})

@app.route("/api/pipeline")
def get_pipeline():
    return jsonify({"stages": PIPELINE_STAGES, "examples": PIPELINE_EXAMPLES})

@app.route("/api/query", methods=["POST"])
def query_video():
    data = request.get_json() or {}
    query = data.get("query", "").lower()
    
    if "goku" in query:
        response = DEMO_QUERY_RESPONSES["goku"]
    elif "vegeta" in query:
        response = DEMO_QUERY_RESPONSES["vegeta"]
    else:
        response = DEMO_QUERY_RESPONSES["default"]
    
    return jsonify({
        "answer": response["answer"],
        "segments": response["segments"],
        "group_id": "demo_group_123"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
