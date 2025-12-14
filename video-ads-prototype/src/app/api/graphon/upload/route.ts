import { NextRequest, NextResponse } from 'next/server';

const GRAPHON_API_URL = 'https://api.graphon.ai';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    const apiKey = process.env.GRAPHON_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Graphon API key not configured' }, { status: 500 });
    }

    // Step 1: Get upload URL
    const uploadUrlResponse = await fetch(`${GRAPHON_API_URL}/v1/files/upload-url`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_name: file.name,
        content_type: file.type,
      }),
    });

    if (!uploadUrlResponse.ok) {
      const error = await uploadUrlResponse.text();
      console.error('Failed to get upload URL:', error);
      return NextResponse.json({ error: 'Failed to get upload URL' }, { status: 500 });
    }

    const { upload_url, file_id } = await uploadUrlResponse.json();

    // Step 2: Upload the file
    const fileBuffer = await file.arrayBuffer();
    const uploadResponse = await fetch(upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
      },
      body: fileBuffer,
    });

    if (!uploadResponse.ok) {
      console.error('Failed to upload file');
      return NextResponse.json({ error: 'Failed to upload file' }, { status: 500 });
    }

    // Step 3: Start processing
    const processResponse = await fetch(`${GRAPHON_API_URL}/v1/files/${file_id}/process`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
      },
    });

    if (!processResponse.ok) {
      console.error('Failed to start processing');
      return NextResponse.json({ error: 'Failed to start processing' }, { status: 500 });
    }

    return NextResponse.json({ 
      success: true, 
      file_id,
      file_name: file.name,
    });
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

