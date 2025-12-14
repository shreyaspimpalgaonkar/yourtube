'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface CutDetectionProps {
  fileId: string | null;
  onCutsDetected: () => void;
}

export default function CutDetection({ fileId, onCutsDetected }: CutDetectionProps) {
  const [detecting, setDetecting] = useState(false);
  const [snippets, setSnippets] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    // Load existing snippets
    loadSnippets();
  }, []);

  const loadSnippets = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/snippets');
      setSnippets(response.data.snippets || []);
    } catch (err) {
      // Ignore errors - snippets might not exist yet
    }
  };

  const handleDetectCuts = async () => {
    if (!fileId) {
      setError('Please upload a video first');
      return;
    }

    setDetecting(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/detect-cuts', {
        file_id: fileId,
      });

      const newJobId = response.data.job_id;
      setJobId(newJobId);

      // Poll for status
      const pollStatus = async () => {
        try {
          const statusResponse = await axios.get(`http://localhost:8000/api/status/${newJobId}`);
          const status = statusResponse.data.status;

          if (status === 'completed') {
            setDetecting(false);
            setSnippets(statusResponse.data.snippets || []);
            loadSnippets();
            onCutsDetected();
          } else if (status === 'failed') {
            setDetecting(false);
            setError(statusResponse.data.message);
          } else {
            setTimeout(pollStatus, 2000);
          }
        } catch (err) {
          setDetecting(false);
          setError('Failed to check status');
        }
      };

      pollStatus();
    } catch (err: any) {
      setDetecting(false);
      setError(err.response?.data?.detail || 'Cut detection failed');
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Detect Scene Cuts</h2>

      <div className="space-y-4">
        <p className="text-gray-600">
          Analyze the video to detect scene cuts and split into snippets.
        </p>

        <button
          onClick={handleDetectCuts}
          disabled={detecting || !fileId}
          className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {detecting ? 'Detecting cuts...' : '✂️ Detect Cuts'}
        </button>

        {detecting && jobId && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800">Processing... (checking status)</p>
          </div>
        )}

        {snippets.length > 0 && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-bold text-lg mb-2">
              ✅ Found {snippets.length} snippet(s)
            </h3>
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">#</th>
                    <th className="text-left p-2">Start Frame</th>
                    <th className="text-left p-2">End Frame</th>
                    <th className="text-left p-2">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {snippets.map((snippet, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="p-2">{snippet.snippet_number}</td>
                      <td className="p-2">{snippet.start_frame}</td>
                      <td className="p-2">{snippet.end_frame}</td>
                      <td className="p-2">{snippet.duration?.toFixed(2)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">❌ Error: {error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

