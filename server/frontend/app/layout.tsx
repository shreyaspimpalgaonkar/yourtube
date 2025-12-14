import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Video Ads Processing Pipeline',
  description: 'Upload, query, and brand videos with AI',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

