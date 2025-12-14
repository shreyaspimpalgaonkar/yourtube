'use client';

import { useState } from 'react';
import axios from 'axios';

interface VideoQueryProps {
  onGroupIdReceived: (groupId: string) => void;
  groupId: string | null;
  fileId: string | null;
}

export default function VideoQuery({ onGroupIdReceived, groupId, fileId }: VideoQueryProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleIngest = async () => {
    setIngesting(true);
    setError(null);

    try {
      if (!fileId) {
        setError('Please upload a video first');
        setIngesting(false);
        return;
      }

      const response = await axios.post('http://localhost:8000/api/ingest', {
        file_id: fileId,
      });

      // Poll for status
      const jobId = response.data.job_id;
      const pollStatus = async () => {
        const statusResponse = await axios.get(`http://localhost:8000/api/status/${jobId}`);
        if (statusResponse.data.status === 'completed') {
          setIngesting(false);
          // Extract group_id from cache or response
          onGroupIdReceived('group_id_placeholder');
        } else if (statusResponse.data.status === 'failed') {
          setIngesting(false);
          setError(statusResponse.data.message);
        } else {
          setTimeout(pollStatus, 2000);
        }
      };
      pollStatus();
    } catch (err: any) {
      setIngesting(false);
      setError(err.response?.data?.detail || 'Ingestion failed');
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/query', {
        query,
        group_id: groupId,
      });

      setResult(response.data);
      if (response.data.group_id && !groupId) {
        onGroupIdReceived(response.data.group_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Query Video</h2>

      {!groupId && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800 mb-2">
            ⚠️ No processed video found. Please ingest a video first.
          </p>
          <button
            onClick={handleIngest}
            disabled={ingesting}
            className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
          >
            {ingesting ? 'Ingesting...' : 'Ingest Video'}
          </button>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enter your query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., When does Michael Scott appear? What happens during the fire drill?"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
          />
        </div>

        <button
          onClick={handleQuery}
          disabled={loading || !query.trim()}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Querying...' : '🔍 Query Video'}
        </button>
      </div>

      {result && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-bold text-lg mb-2">Answer:</h3>
          <p className="text-gray-800 mb-4">{result.answer}</p>

          {result.segments && result.segments.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Found {result.segments.length} segment(s):</h4>
              <ul className="space-y-2">
                {result.segments.map((seg: any, idx: number) => (
                  <li key={idx} className="text-sm text-gray-700">
                    [{idx + 1}] {seg.start_time_formatted} → {seg.end_time_formatted}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">❌ Error: {error}</p>
        </div>
      )}
    </div>
  );
}

