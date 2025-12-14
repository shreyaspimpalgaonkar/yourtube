import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const CACHE_FILE = path.join(process.cwd(), '.graphon-cache.json');

interface CacheData {
  [videoName: string]: {
    file_id: string;
    group_id: string;
    created_at: string;
  };
}

async function readCache(): Promise<CacheData> {
  try {
    const data = await fs.readFile(CACHE_FILE, 'utf-8');
    return JSON.parse(data);
  } catch {
    return {};
  }
}

async function writeCache(cache: CacheData): Promise<void> {
  await fs.writeFile(CACHE_FILE, JSON.stringify(cache, null, 2));
}

// GET - Read cache for a video
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const videoName = searchParams.get('videoName');

    if (!videoName) {
      return NextResponse.json({ error: 'Video name required' }, { status: 400 });
    }

    const cache = await readCache();
    const cached = cache[videoName];

    if (cached) {
      return NextResponse.json({
        cached: true,
        file_id: cached.file_id,
        group_id: cached.group_id,
        created_at: cached.created_at,
      });
    }

    return NextResponse.json({ cached: false });
  } catch (error) {
    console.error('Cache read error:', error);
    return NextResponse.json({ error: 'Failed to read cache' }, { status: 500 });
  }
}

// POST - Save to cache
export async function POST(request: NextRequest) {
  try {
    const { videoName, file_id, group_id } = await request.json();

    if (!videoName || !file_id || !group_id) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const cache = await readCache();
    cache[videoName] = {
      file_id,
      group_id,
      created_at: new Date().toISOString(),
    };
    await writeCache(cache);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Cache write error:', error);
    return NextResponse.json({ error: 'Failed to write cache' }, { status: 500 });
  }
}

// DELETE - Clear cache for a video
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const videoName = searchParams.get('videoName');

    if (!videoName) {
      // Clear all cache
      await writeCache({});
      return NextResponse.json({ success: true, message: 'All cache cleared' });
    }

    const cache = await readCache();
    delete cache[videoName];
    await writeCache(cache);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Cache delete error:', error);
    return NextResponse.json({ error: 'Failed to delete cache' }, { status: 500 });
  }
}

