import { NextRequest, NextResponse } from 'next/server';

const GRAPHON_API_URL = 'https://api.graphon.ai';

// Helper to convert seconds to MM:SS format
function secondsToMMSS(seconds: number | undefined): string {
  if (seconds === undefined || seconds === null) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Structured segment matching Pydantic model
interface StructuredSegment {
  reasoning: string;
  start_time: string;  // MM:SS format
  end_time: string;    // MM:SS format
  start_seconds: number;
  end_seconds: number;
}

// Structured output matching Pydantic GraphonOutput model
interface GraphonOutput {
  query: string;
  answer: string;
  segments: StructuredSegment[];
}

export async function POST(request: NextRequest) {
  try {
    const { groupId, query } = await request.json();

    if (!groupId || !query) {
      return NextResponse.json({ error: 'Group ID and query required' }, { status: 400 });
    }

    const apiKey = process.env.GRAPHON_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Graphon API key not configured' }, { status: 500 });
    }

    const response = await fetch(`${GRAPHON_API_URL}/v1/groups/${groupId}/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        return_source_data: true,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Query failed:', error);
      return NextResponse.json({ error: 'Query failed' }, { status: 500 });
    }

    const queryResult = await response.json();
    
    // Parse into structured format
    const videoSources = (queryResult.sources || []).filter(
      (s: { node_type: string }) => s.node_type === 'video'
    );
    
    const structuredSegments: StructuredSegment[] = videoSources.map(
      (source: { start_time?: number; end_time?: number; text?: string; video_name?: string }) => ({
        reasoning: source.text || `Video segment from ${source.video_name || 'video'}`,
        start_time: secondsToMMSS(source.start_time),
        end_time: secondsToMMSS(source.end_time),
        start_seconds: source.start_time || 0,
        end_seconds: source.end_time || 0,
      })
    );
    
    const structuredOutput: GraphonOutput = {
      query,
      answer: queryResult.answer,
      segments: structuredSegments,
    };
    
    // Return both legacy format and new structured format
    return NextResponse.json({
      // Legacy format for backwards compatibility
      answer: queryResult.answer,
      sources: queryResult.sources || [],
      attention_nodes: queryResult.attention_nodes || [],
      // New structured format
      structured: structuredOutput,
    });
  } catch (error) {
    console.error('Query error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

