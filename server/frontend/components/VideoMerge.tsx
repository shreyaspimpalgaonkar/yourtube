'use client';

import { useState } from 'react';
import axios from 'axios';

export default function VideoMerge() {
  const [merging, setMerging] = useState(false);
  const [outputName, setOutputName] = useState('branded_video.mp4');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [outputPath, setOutputPath] = useState<string | null>(null);

  const handleMerge = async () => {
    setMerging(true);
    setError(null);
    setOutputPath(null);

    try {
      const response = await axios.post('http://localhost:8000/api/merge', {
        output_name: outputName || undefined,
      });

      const newJobId = response.data.job_id;
      setJobId(newJobId);

      // Poll for status
      const pollStatus = async () => {
        try {
          const statusResponse = await axios.get(`http://localhost:8000/api/status/${newJobId}`);
          const status = statusResponse.data.status;

          if (status === 'completed') {
            setMerging(false);
            setOutputPath(statusResponse.data.output_path);
            alert('Video merge completed!');
          } else if (status === 'failed') {
            setMerging(false);
            setError(statusResponse.data.message);
          } else {
            setTimeout(pollStatus, 3000);
          }
        } catch (err) {
          setMerging(false);
          setError('Failed to check status');
        }
      };

      pollStatus();
    } catch (err: any) {
      setMerging(false);
      setError(err.response?.data?.detail || 'Merge failed');
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Merge Video</h2>

      <div className="space-y-6">
        <p className="text-gray-600">
          Merge all processed snippets into a final branded video.
        </p>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Output Filename (optional)
          </label>
          <input
            type="text"
            value={outputName}
            onChange={(e) => setOutputName(e.target.value)}
            placeholder="branded_video.mp4"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={handleMerge}
          disabled={merging}
          className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {merging ? 'Merging...' : '🔗 Merge Video'}
        </button>

        {merging && jobId && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800">
              Merging videos... This may take several minutes. Checking status...
            </p>
            <p className="text-sm text-blue-600 mt-1">Job ID: {jobId}</p>
          </div>
        )}

        {outputPath && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 font-semibold mb-2">
              ✅ Video merge completed!
            </p>
            <p className="text-sm text-green-700">
              Output: {outputPath}
            </p>
            <a
              href={`http://localhost:8000/api/output/${outputPath.split('/').pop()}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-block px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Download Video
            </a>
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

