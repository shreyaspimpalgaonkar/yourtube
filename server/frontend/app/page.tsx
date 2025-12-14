'use client';

import { useState } from 'react';
import VideoUpload from '@/components/VideoUpload';
import VideoQuery from '@/components/VideoQuery';
import CutDetection from '@/components/CutDetection';
import SnippetProcessing from '@/components/SnippetProcessing';
import VideoMerge from '@/components/VideoMerge';
import VideoPlayer from '@/components/VideoPlayer';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'query' | 'cuts' | 'process' | 'merge'>('upload');
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [groupId, setGroupId] = useState<string | null>(null);

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          🎬 Video Ads Processing Pipeline
        </h1>
        <p className="text-gray-600 mb-8">
          Upload videos, query with AI, detect cuts, add branding, and merge into final videos
        </p>

        {/* Tab Navigation */}
        <div className="flex space-x-2 mb-8 border-b border-gray-300">
          {[
            { id: 'upload', label: '📤 Upload Video' },
            { id: 'query', label: '🔍 Query Video' },
            { id: 'cuts', label: '✂️ Detect Cuts' },
            { id: 'process', label: '🎨 Process Snippets' },
            { id: 'merge', label: '🔗 Merge Video' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {activeTab === 'upload' && (
            <VideoUpload
              onUploadSuccess={(fileId) => {
                setUploadedFileId(fileId);
                setActiveTab('query');
              }}
            />
          )}

          {activeTab === 'query' && (
            <VideoQuery
              onGroupIdReceived={setGroupId}
              groupId={groupId}
              fileId={uploadedFileId}
            />
          )}

          {activeTab === 'cuts' && (
            <CutDetection
              fileId={uploadedFileId}
              onCutsDetected={() => setActiveTab('process')}
            />
          )}

          {activeTab === 'process' && (
            <SnippetProcessing />
          )}

          {activeTab === 'merge' && (
            <VideoMerge />
          )}
        </div>

        {/* Video Player */}
        {uploadedFileId && (
          <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">Video Preview</h2>
            <VideoPlayer fileId={uploadedFileId} />
          </div>
        )}
      </div>
    </main>
  );
}

