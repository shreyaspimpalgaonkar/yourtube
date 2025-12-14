import { NextRequest, NextResponse } from 'next/server';

const GRAPHON_API_URL = 'https://api.graphon.ai';

export async function POST(request: NextRequest) {
  try {
    const { fileIds, groupName } = await request.json();

    if (!fileIds || !Array.isArray(fileIds) || fileIds.length === 0) {
      return NextResponse.json({ error: 'File IDs required' }, { status: 400 });
    }

    const apiKey = process.env.GRAPHON_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Graphon API key not configured' }, { status: 500 });
    }

    const response = await fetch(`${GRAPHON_API_URL}/v1/groups`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_ids: fileIds,
        group_name: groupName || 'Video Analysis Group',
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Failed to create group:', error);
      return NextResponse.json({ error: 'Failed to create group' }, { status: 500 });
    }

    const groupData = await response.json();
    
    return NextResponse.json({
      group_id: groupData.group_id,
      group_name: groupData.group_name,
      graph_status: groupData.graph_status,
    });
  } catch (error) {
    console.error('Group creation error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const groupId = searchParams.get('groupId');

    if (!groupId) {
      return NextResponse.json({ error: 'Group ID required' }, { status: 400 });
    }

    const apiKey = process.env.GRAPHON_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Graphon API key not configured' }, { status: 500 });
    }

    const response = await fetch(`${GRAPHON_API_URL}/v1/groups/${groupId}`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
      },
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'Failed to get group status' }, { status: 500 });
    }

    const groupData = await response.json();
    
    return NextResponse.json({
      group_id: groupData.group_id,
      group_name: groupData.group_name,
      graph_status: groupData.graph_status,
    });
  } catch (error) {
    console.error('Group status error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

