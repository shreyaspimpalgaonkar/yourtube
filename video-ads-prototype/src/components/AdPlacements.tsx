'use client';

import { useState } from 'react';
import { AdPlacement, VideoSegment } from '@/types';

interface AdPlacementsProps {
  segments: VideoSegment[];
  onGenerateAd: (placement: AdPlacement) => void;
}

const AD_PRESETS = [
  { character: 'Michael Scott', brand: 'Red Bull', color: '#ef4444' },
  { character: 'Andy Bernard', brand: 'Corn Syrup', color: '#f59e0b' },
  { character: 'Dwight Schrute', brand: 'Adidas', color: '#3b82f6' },
];

export default function AdPlacements({ segments, onGenerateAd }: AdPlacementsProps) {
  const [placements, setPlacements] = useState<AdPlacement[]>([]);
  const [customBrand, setCustomBrand] = useState('');
  const [customCharacter, setCustomCharacter] = useState('');

  const addPlacementFromSegment = (segment: VideoSegment, preset: typeof AD_PRESETS[0]) => {
    const newPlacement: AdPlacement = {
      id: `ad-${Date.now()}-${Math.random()}`,
      character: preset.character,
      brand: preset.brand,
      startTime: segment.start_time || 0,
      endTime: segment.end_time || 0,
    };
    
    setPlacements(prev => [...prev, newPlacement]);
  };

  const addCustomPlacement = (segment: VideoSegment) => {
    if (!customBrand.trim() || !customCharacter.trim()) return;
    
    const newPlacement: AdPlacement = {
      id: `ad-${Date.now()}-${Math.random()}`,
      character: customCharacter.trim(),
      brand: customBrand.trim(),
      startTime: segment.start_time || 0,
      endTime: segment.end_time || 0,
    };
    
    setPlacements(prev => [...prev, newPlacement]);
    setCustomBrand('');
    setCustomCharacter('');
  };

  const removePlacement = (id: string) => {
    setPlacements(prev => prev.filter(p => p.id !== id));
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getPresetColor = (brand: string) => {
    const preset = AD_PRESETS.find(p => p.brand === brand);
    return preset?.color || '#a855f7';
  };

  return (
    <div className="space-y-6">
      {/* Available segments to add ads */}
      {segments.length > 0 ? (
        <div className="space-y-4">
          <p className="text-sm text-[var(--text-muted)]">
            Found {segments.length} segment{segments.length !== 1 ? 's' : ''} - select a brand for each:
          </p>
          
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {segments.map((segment, i) => (
              segment.node_type === 'video' && (
                <div
                  key={i}
                  className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium">
                      <span className="font-mono text-[var(--accent-secondary)]">
                        {formatTime(segment.start_time || 0)}
                      </span>
                      <span className="text-[var(--text-muted)]"> — </span>
                      <span className="font-mono text-[var(--accent-secondary)]">
                        {formatTime(segment.end_time || 0)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Preset brand buttons */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {AD_PRESETS.map((preset, j) => (
                      <button
                        key={j}
                        onClick={() => addPlacementFromSegment(segment, preset)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:scale-105"
                        style={{ 
                          backgroundColor: `${preset.color}20`,
                          color: preset.color,
                          border: `1px solid ${preset.color}40`
                        }}
                      >
                        + {preset.brand}
                      </button>
                    ))}
                  </div>
                  
                  {/* Custom brand input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customCharacter}
                      onChange={(e) => setCustomCharacter(e.target.value)}
                      placeholder="Character..."
                      className="flex-1 px-2 py-1.5 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)] 
                               text-xs focus:outline-none focus:border-[var(--accent-tertiary)]"
                    />
                    <input
                      type="text"
                      value={customBrand}
                      onChange={(e) => setCustomBrand(e.target.value)}
                      placeholder="Brand..."
                      className="flex-1 px-2 py-1.5 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)] 
                               text-xs focus:outline-none focus:border-[var(--accent-tertiary)]"
                    />
                    <button
                      onClick={() => addCustomPlacement(segment)}
                      disabled={!customBrand.trim() || !customCharacter.trim()}
                      className="px-3 py-1.5 rounded-lg bg-[var(--accent-tertiary)] text-white text-xs
                               hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      +
                    </button>
                  </div>
                </div>
              )
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-[var(--text-muted)] text-sm">
          <p className="mb-2">👆 Query the video first to find scenes</p>
          <p>Try: "When does Michael appear?"</p>
        </div>
      )}

      {/* Current placements queue */}
      {placements.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-[var(--border)]">
          <h4 className="text-sm font-medium">
            Ad Queue ({placements.length})
          </h4>
          
          <div className="space-y-2">
            {placements.map((placement) => (
              <div
                key={placement.id}
                className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface)] 
                         border transition-all"
                style={{ borderColor: `${getPresetColor(placement.brand)}40` }}
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="w-2 h-8 rounded-full"
                    style={{ backgroundColor: getPresetColor(placement.brand) }}
                  />
                  <div>
                    <div className="text-sm font-medium">{placement.brand}</div>
                    <div className="text-xs text-[var(--text-muted)]">
                      {placement.character} • {formatTime(placement.startTime)}-{formatTime(placement.endTime)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => removePlacement(placement.id)}
                  className="p-1.5 rounded-lg hover:bg-red-500/20 text-red-400 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
          
          <button
            onClick={() => placements.forEach(p => onGenerateAd(p))}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-[var(--accent-primary)] via-[var(--accent-secondary)]
                     to-[var(--accent-tertiary)] text-white font-medium hover:opacity-90 transition-opacity
                     animate-pulse-glow"
          >
            🚀 Generate {placements.length} Ad{placements.length !== 1 ? 's' : ''} with Veo 3.1
          </button>
        </div>
      )}
    </div>
  );
}
