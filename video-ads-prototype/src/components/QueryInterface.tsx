'use client';

import { useState } from 'react';
import { QueryResult, VideoSegment } from '@/types';

interface QueryInterfaceProps {
  groupId: string | null;
  onQueryResult: (result: QueryResult) => void;
  onSegmentClick: (segment: VideoSegment) => void;
}

export default function QueryInterface({ 
  groupId, 
  onQueryResult,
  onSegmentClick 
}: QueryInterfaceProps) {
  const [query, setQuery] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [results, setResults] = useState<QueryResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<string[]>([]);

  const suggestedQueries = [
    "When does Michael Scott appear?",
    "What happens during the fire drill?",
    "When is Dwight on screen?",
    "Find all scenes with Andy Bernard",
    "When do people panic in the video?",
    "Show me the funniest moments"
  ];

  const handleQuery = async () => {
    if (!query.trim() || !groupId) return;

    setIsQuerying(true);
    try {
      const response = await fetch('/api/graphon/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groupId, query: query.trim() }),
      });

      if (!response.ok) throw new Error('Query failed');

      const result: QueryResult = await response.json();
      setResults(result);
      onQueryResult(result);
      setQueryHistory(prev => [query, ...prev.slice(0, 4)]);
    } catch (error) {
      console.error('Query error:', error);
    } finally {
      setIsQuerying(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Query input */}
      <div className="space-y-3">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            placeholder="Ask about the video... e.g., 'When does Michael appear?'"
            className="flex-1 px-4 py-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] 
                     focus:border-[var(--accent-secondary)] focus:outline-none focus:ring-2 
                     focus:ring-[var(--accent-secondary)]/20 transition-all"
            disabled={!groupId || isQuerying}
          />
          <button
            onClick={handleQuery}
            disabled={!query.trim() || !groupId || isQuerying}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-[var(--accent-secondary)] to-[var(--accent-tertiary)]
                     text-white font-medium hover:opacity-90 transition-opacity flex items-center gap-2
                     disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px] justify-center"
          >
            {isQuerying ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Query
              </>
            )}
          </button>
        </div>

        {/* Suggested queries */}
        {!groupId && (
          <p className="text-[var(--text-muted)] text-sm flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-[var(--accent-secondary)] border-t-transparent rounded-full animate-spin" />
            Initializing video analysis...
          </p>
        )}
        
        {groupId && !results && (
          <div className="flex flex-wrap gap-2">
            {suggestedQueries.map((suggestion, i) => (
              <button
                key={i}
                onClick={() => setQuery(suggestion)}
                className="px-3 py-1.5 rounded-lg bg-[var(--surface)] text-sm text-[var(--text-muted)]
                         hover:text-white hover:bg-[var(--surface-elevated)] transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4 animate-slide-up">
          {/* Answer */}
          <div className="p-4 rounded-xl bg-[var(--surface-elevated)] border border-[var(--border)]">
            <h3 className="text-sm font-medium text-[var(--text-muted)] mb-2">Answer</h3>
            <p className="text-lg">{results.answer}</p>
          </div>

          {/* Video segments */}
          {results.sources.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-[var(--text-muted)]">
                Found {results.sources.length} relevant segment{results.sources.length !== 1 ? 's' : ''}
              </h3>
              
              <div className="grid gap-3">
                {results.sources.map((source, i) => (
                  source.node_type === 'video' && (
                    <button
                      key={i}
                      onClick={() => onSegmentClick(source)}
                      className="flex items-center gap-4 p-4 rounded-xl bg-[var(--surface)] 
                               border border-[var(--border)] hover:border-[var(--accent-primary)]
                               transition-all group text-left"
                    >
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--accent-primary)] 
                                    to-[var(--accent-secondary)] flex items-center justify-center
                                    group-hover:scale-110 transition-transform">
                        <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                      
                      <div className="flex-1">
                        <div className="font-medium">
                          {formatTime(source.start_time || 0)} — {formatTime(source.end_time || 0)}
                        </div>
                        <div className="text-sm text-[var(--text-muted)]">
                          {source.video_name || 'Video segment'}
                        </div>
                      </div>
                      
                      <div className="text-[var(--accent-primary)] opacity-0 group-hover:opacity-100 transition-opacity">
                        Jump to →
                      </div>
                    </button>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Query history */}
      {queryHistory.length > 0 && (
        <div className="pt-4 border-t border-[var(--border)]">
          <h4 className="text-xs font-medium text-[var(--text-muted)] mb-2">Recent queries</h4>
          <div className="flex flex-wrap gap-2">
            {queryHistory.map((q, i) => (
              <button
                key={i}
                onClick={() => setQuery(q)}
                className="px-2 py-1 rounded-md bg-[var(--surface)] text-xs text-[var(--text-muted)]
                         hover:text-white transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

