export interface VideoSource {
  id: string;
  name: string;
  url: string;
  file?: File;
}

// New structured segment format (matches Pydantic model)
export interface StructuredSegment {
  reasoning: string;
  start_time: string;  // MM:SS format
  end_time: string;    // MM:SS format
  start_seconds?: number;
  end_seconds?: number;
}

// Structured output format (matches Pydantic GraphonOutput)
export interface GraphonOutput {
  query: string;
  answer: string;
  segments: StructuredSegment[];
}

// Legacy format for backwards compatibility
export interface QueryResult {
  answer: string;
  sources: VideoSegment[];
  // New structured format
  structured?: GraphonOutput;
}

export interface VideoSegment {
  node_type: 'video' | 'document' | 'image';
  video_name?: string;
  start_time?: number;
  end_time?: number;
  time_limited_url?: string;
  pdf_name?: string;
  page_num?: number;
  text?: string;
  image_name?: string;
  reasoning?: string;  // Added for structured output
}

export interface ProcessingStatus {
  status: 'idle' | 'uploading' | 'processing' | 'ready' | 'error';
  message: string;
  progress?: number;
}

export interface AdPlacement {
  id: string;
  character: string;
  brand: string;
  startTime: number;
  endTime: number;
  prompt?: string;
}

export interface GraphonFile {
  file_id: string;
  file_name: string;
  file_type: string;
  processing_status: 'UNPROCESSED' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  error_message?: string;
}

export interface GraphonGroup {
  group_id: string;
  group_name: string;
  graph_status: 'pending' | 'building' | 'ready' | 'failed';
}

