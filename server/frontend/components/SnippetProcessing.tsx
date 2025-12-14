'use client';

import { useState } from 'react';
import axios from 'axios';

export default function SnippetProcessing() {
  const [snippetNumber, setSnippetNumber] = useState<number | null>(null);
  const [processAll, setProcessAll] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async () => {
    setProcessing(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/process-snippet', {
        snippet_number: processAll ? null : snippetNumber,
        process_all: processAll,
      });

      const newJobId = response.data.job_id;
      setJobId(newJobId);

      // Poll for status
      const pollStatus = async () => {
        try {
          const statusResponse = await axios.get(`http://localhost:8000/api/status/${newJobId}`);
          const status = statusResponse.data.status;

          if (status === 'completed') {
            setProcessing(false);
            alert('Snippet processing completed!');
          } else if (status === 'failed') {
            setProcessing(false);
            setError(statusResponse.data.message);
          } else {
            setTimeout(pollStatus, 3000);
          }
        } catch (err) {
          setProcessing(false);
          setError('Failed to check status');
        }
      };

      pollStatus();
    } catch (err: any) {
      setProcessing(false);
      setError(err.response?.data?.detail || 'Processing failed');
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Process Snippets</h2>

      <div className="space-y-6">
        <p className="text-gray-600">
          Add branding logos to video snippets using AI. Process individual snippets or all at once.
        </p>

        <div className="space-y-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={processAll}
              onChange={(e) => setProcessAll(e.target.checked)}
              className="w-4 h-4"
            />
            <span>Process all snippets</span>
          </label>

          {!processAll && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Snippet Number
              </label>
              <input
                type="number"
                value={snippetNumber || ''}
                onChange={(e) => setSnippetNumber(parseInt(e.target.value) || null)}
                placeholder="e.g., 8"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="1"
              />
              <p className="text-sm text-gray-500 mt-1">
                Goku snippets: 8, 11, 17, 19, 24, 29 | Vegeta snippets: 18, 23
              </p>
            </div>
          )}

          <button
            onClick={handleProcess}
            disabled={processing || (!processAll && !snippetNumber)}
            className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processing ? 'Processing...' : '🎨 Process Snippet(s)'}
          </button>
        </div>

        {processing && jobId && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800">
              Processing... This may take several minutes. Checking status...
            </p>
            <p className="text-sm text-blue-600 mt-1">Job ID: {jobId}</p>
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

