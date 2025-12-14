'use client';

import { useState, useCallback, useEffect } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import QueryInterface from '@/components/QueryInterface';
import AdPlacements from '@/components/AdPlacements';
import { ProcessingStatus, QueryResult, VideoSegment, AdPlacement } from '@/types';

const VIDEO_NAME = 'office.mp4';

export default function Home() {
  const [groupId, setGroupId] = useState<string | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    status: 'idle',
    message: '',
  });
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [querySegments, setQuerySegments] = useState<VideoSegment[]>([]);
  const [generatingAds, setGeneratingAds] = useState<string[]>([]);

  // Poll for file processing status
  const pollFileStatus = useCallback(async (fileId: string): Promise<boolean> => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async (): Promise<boolean> => {
      attempts++;
      try {
        const response = await fetch(`/api/graphon/status?fileId=${fileId}`);
        if (!response.ok) throw new Error('Status check failed');
        
        const data = await response.json();
        
        if (data.processing_status === 'SUCCESS') {
          return true;
        } else if (data.processing_status === 'FAILURE') {
          throw new Error(data.error_message || 'Processing failed');
        } else if (attempts >= maxAttempts) {
          throw new Error('Processing timeout');
        }
        
        setProcessingStatus({
          status: 'processing',
          message: `Processing video... (${Math.round((attempts / maxAttempts) * 100)}%)`,
          progress: (attempts / maxAttempts) * 50,
        });
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        return poll();
      } catch (error) {
        throw error;
      }
    };

    return poll();
  }, []);

  // Poll for group building status
  const pollGroupStatus = useCallback(async (groupId: string): Promise<boolean> => {
    const maxAttempts = 120;
    let attempts = 0;

    const poll = async (): Promise<boolean> => {
      attempts++;
      try {
        const response = await fetch(`/api/graphon/group?groupId=${groupId}`);
        if (!response.ok) throw new Error('Group status check failed');
        
        const data = await response.json();
        
        if (data.graph_status === 'ready') {
          return true;
        } else if (data.graph_status === 'failed') {
          throw new Error('Graph building failed');
        } else if (attempts >= maxAttempts) {
          throw new Error('Graph building timeout');
        }
        
        setProcessingStatus({
          status: 'processing',
          message: `Building knowledge graph... (${Math.round(50 + (attempts / maxAttempts) * 50)}%)`,
          progress: 50 + (attempts / maxAttempts) * 50,
        });
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        return poll();
      } catch (error) {
        throw error;
      }
    };

    return poll();
  }, []);

  // Initialize video - check cache first, then process if needed
  useEffect(() => {
    const initializeVideo = async () => {
      setProcessingStatus({
        status: 'processing',
        message: 'Checking cache...',
        progress: 5,
      });

      try {
        // Check if we have cached data for this video
        const cacheResponse = await fetch(`/api/graphon/cache?videoName=${VIDEO_NAME}`);
        const cacheData = await cacheResponse.json();

        if (cacheData.cached) {
          // Verify the group is still valid
          setProcessingStatus({
            status: 'processing',
            message: 'Found cached data, verifying...',
            progress: 50,
          });

          try {
            const groupResponse = await fetch(`/api/graphon/group?groupId=${cacheData.group_id}`);
            const groupData = await groupResponse.json();

            if (groupData.graph_status === 'ready') {
              setFileId(cacheData.file_id);
              setGroupId(cacheData.group_id);
              setProcessingStatus({
                status: 'ready',
                message: `Video ready! (cached from ${new Date(cacheData.created_at).toLocaleDateString()})`,
              });
              return;
            }
          } catch (e) {
            console.log('Cached group invalid, re-processing...');
          }
        }

        // No valid cache - need to process the video
        setProcessingStatus({
          status: 'processing',
          message: 'Uploading video to Graphon...',
          progress: 10,
        });

        // Read the video file from public folder and upload it
        const videoResponse = await fetch(`/${VIDEO_NAME}`);
        const videoBlob = await videoResponse.blob();
        const videoFile = new File([videoBlob], VIDEO_NAME, { type: 'video/mp4' });

        const formData = new FormData();
        formData.append('file', videoFile);

        const uploadResponse = await fetch('/api/graphon/upload', {
          method: 'POST',
          body: formData,
        });

        if (!uploadResponse.ok) {
          throw new Error('Upload failed');
        }

        const { file_id } = await uploadResponse.json();
        setFileId(file_id);

        setProcessingStatus({
          status: 'processing',
          message: 'Processing video with AI...',
          progress: 20,
        });

        // Poll until processing is complete
        await pollFileStatus(file_id);

        setProcessingStatus({
          status: 'processing',
          message: 'Creating knowledge graph...',
          progress: 55,
        });

        // Create group
        const groupResponse = await fetch('/api/graphon/group', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fileIds: [file_id],
            groupName: `Video Analysis - ${VIDEO_NAME}`,
          }),
        });

        if (!groupResponse.ok) {
          throw new Error('Failed to create group');
        }

        const { group_id } = await groupResponse.json();
        setGroupId(group_id);

        // Poll until graph is ready
        await pollGroupStatus(group_id);

        // Save to cache
        await fetch('/api/graphon/cache', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            videoName: VIDEO_NAME,
            file_id,
            group_id,
          }),
        });

        setProcessingStatus({
          status: 'ready',
          message: 'Video ready for queries!',
        });
      } catch (error) {
        console.error('Error initializing video:', error);
        setProcessingStatus({
          status: 'error',
          message: error instanceof Error ? error.message : 'Failed to process video',
        });
      }
    };

    initializeVideo();
  }, [pollFileStatus, pollGroupStatus]);

  const handleQueryResult = useCallback((result: QueryResult) => {
    const videoSegments = result.sources.filter(s => s.node_type === 'video');
    setQuerySegments(videoSegments);
  }, []);

  const handleSegmentClick = useCallback((segment: VideoSegment) => {
    if (segment.start_time !== undefined) {
      setCurrentTime(segment.start_time);
    }
  }, []);

  const handleGenerateAd = useCallback(async (placement: AdPlacement) => {
    setGeneratingAds(prev => [...prev, placement.id]);
    
    try {
      const response = await fetch('/api/veo/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: placement.character,
          brand: placement.brand,
          startTime: placement.startTime,
          endTime: placement.endTime,
        }),
      });

      if (!response.ok) {
        throw new Error('Generation failed');
      }

      const result = await response.json();
      console.log('Ad generation started:', result);
      
      alert(`Ad generation started for ${placement.brand} on ${placement.character}! Check console for details.`);
    } catch (error) {
      console.error('Ad generation error:', error);
      alert('Failed to generate ad. Check console for details.');
    } finally {
      setGeneratingAds(prev => prev.filter(id => id !== placement.id));
    }
  }, []);

  const handleClearCache = async () => {
    if (confirm('Clear cache and re-process video?')) {
      await fetch(`/api/graphon/cache?videoName=${VIDEO_NAME}`, { method: 'DELETE' });
      window.location.reload();
    }
  };

  // Create timeline segments for the video player
  const playerSegments = querySegments.map((seg, i) => ({
    start: seg.start_time || 0,
    end: seg.end_time || 0,
    label: `Segment ${i + 1}`,
    color: ['#ff6b35', '#00d4aa', '#a855f7'][i % 3],
  }));

  return (
    <main className="min-h-screen bg-[var(--background)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] glass sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--accent-primary)] via-[var(--accent-secondary)] to-[var(--accent-tertiary)] flex items-center justify-center">
                <span className="text-xl">🎬</span>
              </div>
              <div>
                <h1 className="text-xl font-bold gradient-text">AdMorph</h1>
                <p className="text-xs text-[var(--text-muted)]">AI-Powered Video Ad Personalization</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                <span className="text-sm">📺</span>
                <span className="text-sm text-[var(--text-muted)]">{VIDEO_NAME}</span>
              </div>
              <button
                onClick={handleClearCache}
                className="px-3 py-1.5 rounded-lg text-xs text-[var(--text-muted)] hover:text-white 
                         hover:bg-[var(--surface)] transition-colors"
                title="Clear cache and re-process"
              >
                🔄 Reset
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column - Video Player & Query */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Player */}
            <div className="animate-slide-up">
              <VideoPlayer 
                src={`/${VIDEO_NAME}`}
                currentTime={currentTime}
                onTimeUpdate={setCurrentTime}
                segments={playerSegments}
              />
            </div>

            {/* Status indicator */}
            {processingStatus.status !== 'ready' && processingStatus.status !== 'idle' && (
              <div className="p-4 rounded-xl bg-[var(--surface-elevated)] border border-[var(--border)]">
                <div className="flex items-center gap-3">
                  {processingStatus.status === 'error' ? (
                    <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-5 h-5 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin" />
                  )}
                  <span className="text-sm">{processingStatus.message}</span>
                </div>
                {processingStatus.progress !== undefined && processingStatus.status !== 'error' && (
                  <div className="mt-3 h-2 bg-[var(--border)] rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)] transition-all duration-300"
                      style={{ width: `${processingStatus.progress}%` }}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Ready status */}
            {processingStatus.status === 'ready' && (
              <div className="p-3 rounded-xl bg-[var(--accent-secondary)]/10 border border-[var(--accent-secondary)]/30">
                <div className="flex items-center gap-2 text-sm text-[var(--accent-secondary)]">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {processingStatus.message}
                </div>
              </div>
            )}

            {/* Query Interface */}
            <div className="p-6 rounded-2xl bg-[var(--surface-elevated)] border border-[var(--border)]">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-[var(--accent-secondary)]/20 flex items-center justify-center">
                  🔍
                </span>
                Step 1: Find Characters & Scenes
              </h2>
              <QueryInterface 
                groupId={groupId}
                onQueryResult={handleQueryResult}
                onSegmentClick={handleSegmentClick}
              />
            </div>
          </div>

          {/* Right column - Ad Placements */}
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-[var(--surface-elevated)] border border-[var(--border)] sticky top-24">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-[var(--accent-primary)]/20 flex items-center justify-center">
                  🎯
                </span>
                Step 2: Place Ads
              </h2>
              <AdPlacements 
                segments={querySegments}
                onGenerateAd={handleGenerateAd}
              />
              
              {/* Generation status */}
              {generatingAds.length > 0 && (
                <div className="mt-6 p-4 rounded-xl bg-[var(--accent-tertiary)]/10 border border-[var(--accent-tertiary)]/30">
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 border-2 border-[var(--accent-tertiary)] border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm">Generating {generatingAds.length} ad{generatingAds.length !== 1 ? 's' : ''}...</span>
                  </div>
                </div>
              )}
            </div>

            {/* How it works */}
            <div className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)]">
              <h3 className="font-semibold mb-4">How it works</h3>
              <div className="space-y-4 text-sm">
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-[var(--accent-secondary)] text-white 
                                flex items-center justify-center text-xs font-bold shrink-0">1</div>
                  <p className="text-[var(--text-muted)]">
                    Ask questions to find specific characters (Michael, Dwight, Andy) or scenes.
                  </p>
                </div>
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-[var(--accent-primary)] text-white 
                                flex items-center justify-center text-xs font-bold shrink-0">2</div>
                  <p className="text-[var(--text-muted)]">
                    Select brands for each character segment from the presets or add custom ones.
                  </p>
                </div>
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-[var(--accent-tertiary)] text-white 
                                flex items-center justify-center text-xs font-bold shrink-0">3</div>
                  <p className="text-[var(--text-muted)]">
                    Generate personalized ads with Veo 3.1 for each placement.
                  </p>
                </div>
              </div>
            </div>

            {/* Ad assignments */}
            <div className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)]">
              <h3 className="font-semibold mb-4">🎯 Target Ad Assignments</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-elevated)]">
                  <span>Michael Scott</span>
                  <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 font-medium">Red Bull</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-elevated)]">
                  <span>Andy Bernard</span>
                  <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-400 font-medium">Corn Syrup</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-elevated)]">
                  <span>Dwight Schrute</span>
                  <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 font-medium">Adidas</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-sm text-[var(--text-muted)]">
            <p>Built with Graphon AI & Google Veo 3.1</p>
            <p>AGI Hackathon 2025</p>
          </div>
        </div>
      </footer>
    </main>
  );
}
