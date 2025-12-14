'use client';

import ReactPlayer from 'react-player';

interface VideoPlayerProps {
  fileId: string;
}

export default function VideoPlayer({ fileId }: VideoPlayerProps) {
  const videoUrl = `http://localhost:8000/api/video/${fileId}`;

  return (
    <div className="w-full">
      <ReactPlayer
        url={videoUrl}
        controls
        width="100%"
        height="auto"
        config={{
          file: {
            attributes: {
              controlsList: 'nodownload',
            },
          },
        }}
      />
    </div>
  );
}

