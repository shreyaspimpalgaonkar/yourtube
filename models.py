"""
Pydantic models for structured Graphon API output.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class VideoSegment(BaseModel):
    """A single video segment with reasoning and timestamps."""
    
    reasoning: str = Field(
        description="Explanation for why this segment was identified as relevant"
    )
    start_time: str = Field(
        description="Start timestamp in MM:SS format",
        examples=["0:15", "1:30", "10:45"]
    )
    end_time: str = Field(
        description="End timestamp in MM:SS format", 
        examples=["0:30", "2:00", "11:15"]
    )
    
    # Optional: keep raw seconds for programmatic use
    start_seconds: Optional[float] = Field(
        default=None,
        description="Start time in raw seconds"
    )
    end_seconds: Optional[float] = Field(
        default=None,
        description="End time in raw seconds"
    )
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Ensure time is in MM:SS format."""
        if ':' not in v:
            raise ValueError(f"Time must be in MM:SS format, got: {v}")
        parts = v.split(':')
        if len(parts) != 2:
            raise ValueError(f"Time must be in MM:SS format, got: {v}")
        return v
    
    @classmethod
    def from_seconds(cls, start: float, end: float, reasoning: str = "") -> "VideoSegment":
        """Create a VideoSegment from seconds."""
        return cls(
            reasoning=reasoning,
            start_time=seconds_to_mmss(start),
            end_time=seconds_to_mmss(end),
            start_seconds=start,
            end_seconds=end,
        )


class GraphonOutput(BaseModel):
    """Structured output from a Graphon video query."""
    
    query: str = Field(
        description="The original query that was asked"
    )
    answer: str = Field(
        description="The natural language answer from Graphon"
    )
    segments: list[VideoSegment] = Field(
        default_factory=list,
        description="List of relevant video segments with timestamps"
    )
    
    def __str__(self) -> str:
        """Pretty print the output."""
        lines = [
            f"Query: {self.query}",
            f"Answer: {self.answer}",
            f"\nSegments ({len(self.segments)}):",
        ]
        for i, seg in enumerate(self.segments, 1):
            lines.append(f"  [{i}] {seg.start_time} - {seg.end_time}")
            if seg.reasoning:
                lines.append(f"      Reasoning: {seg.reasoning}")
        return "\n".join(lines)
    
    def to_json(self, indent: int = 2) -> str:
        """Export as formatted JSON."""
        return self.model_dump_json(indent=indent)


def seconds_to_mmss(seconds: float | None) -> str:
    """Convert seconds to MM:SS format."""
    if seconds is None:
        return "0:00"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def mmss_to_seconds(time_str: str) -> float:
    """Convert MM:SS format to seconds."""
    parts = time_str.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}")
    mins, secs = int(parts[0]), int(parts[1])
    return mins * 60 + secs


def parse_graphon_response(query: str, response) -> GraphonOutput:
    """
    Parse a raw Graphon API response into structured output.
    
    Args:
        query: The original query string
        response: The QueryResponse from Graphon client
        
    Returns:
        GraphonOutput with structured segments
    """
    segments = []
    
    # Extract video sources from the response
    video_sources = [s for s in response.sources if s.get("node_type") == "video"]
    
    for source in video_sources:
        start = source.get("start_time", 0)
        end = source.get("end_time", 0)
        
        # Generate reasoning from the source context if available
        reasoning = source.get("text", "") or source.get("description", "")
        if not reasoning:
            reasoning = f"Video segment from {source.get('video_name', 'video')}"
        
        segment = VideoSegment.from_seconds(
            start=start,
            end=end,
            reasoning=reasoning,
        )
        segments.append(segment)
    
    return GraphonOutput(
        query=query,
        answer=response.answer,
        segments=segments,
    )

