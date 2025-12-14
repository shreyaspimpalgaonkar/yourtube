import { NextRequest, NextResponse } from 'next/server';

const GRAPHON_API_URL = 'https://api.graphon.ai';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const fileId = searchParams.get('fileId');

    if (!fileId) {
      return NextResponse.json({ error: 'File ID required' }, { status: 400 });
    }

    const apiKey = process.env.GRAPHON_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Graphon API key not configured' }, { status: 500 });
    }

    const response = await fetch(`${GRAPHON_API_URL}/v1/files/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
      },
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'Failed to get file status' }, { status: 500 });
    }

    const fileData = await response.json();
    
    return NextResponse.json({
      file_id: fileData.file_id,
      file_name: fileData.file_name,
      processing_status: fileData.processing_status,
      error_message: fileData.error_message,
    });
  } catch (error) {
    console.error('Status check error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

