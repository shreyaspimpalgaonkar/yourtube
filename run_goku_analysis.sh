#!/bin/bash
# Wrapper script to run Goku video ingestion and query
# Usage: ./run_goku_analysis.sh [API_KEY]
# Or set GRAPHON_API_KEY environment variable

set -e

API_KEY="${1:-$GRAPHON_API_KEY}"

if [ -z "$API_KEY" ]; then
    echo "❌ ERROR: GRAPHON_API_KEY not provided"
    echo ""
    echo "Usage:"
    echo "  ./run_goku_analysis.sh YOUR_API_KEY"
    echo "  OR"
    echo "  export GRAPHON_API_KEY='your-api-key'"
    echo "  ./run_goku_analysis.sh"
    echo ""
    exit 1
fi

export GRAPHON_API_KEY="$API_KEY"

echo "🚀 Starting Goku video analysis..."
echo ""

# Step 1: Ingest the video
echo "📤 Step 1: Ingesting goku.mp4..."
uv run ingest_video.py <<< "" || {
    echo "⚠️  Note: If ingestion was already done, this is okay"
}

echo ""
echo "🔍 Step 2: Querying for Goku timestamps..."
echo ""

# Step 2: Query
uv run query_goku.py <<< ""

echo ""
echo "✅ Analysis complete!"

