/**
 * API client for communicating with the FastAPI backend
 */
import type { StreamEvent, StreamCallbacks } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  message: string;
}

/**
 * Stream chat messages from the backend with proper SSE event parsing
 * @param message The user's message
 * @param callbacks Callbacks for different event types
 */
export async function streamChat(
  message: string,
  callbacks: StreamCallbacks
): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          callbacks.onStreamComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE format: "event: <type>\ndata: <json>\n\n"
        const events = buffer.split('\n\n');
        // Keep the last incomplete event in the buffer
        buffer = events.pop() || '';

        for (const eventBlock of events) {
          if (!eventBlock.trim()) continue;

          let eventType = 'message'; // default
          let data = '';

          const lines = eventBlock.split('\n');
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              data = line.slice(6).trim();
            }
          }

          if (!data) continue;

          try {
            const parsedData: StreamEvent = JSON.parse(data);

            // Route to appropriate callback based on event type
            switch (parsedData.type) {
              case 'thought':
                callbacks.onThought?.(parsedData.content);
                break;
              case 'code':
                callbacks.onCodeChunk?.(parsedData.content);
                break;
              case 'data':
                callbacks.onData?.(parsedData.payload);
                break;
              case 'error':
                callbacks.onError?.(parsedData);
                break;
            }
          } catch (parseError) {
            // If JSON parsing fails, treat as plain text chunk (backward compatibility)
            console.warn('Failed to parse SSE event as JSON:', parseError);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    callbacks.onError?.({
      type: 'error',
      message: error instanceof Error ? error.message : String(error),
    });
  }
}

