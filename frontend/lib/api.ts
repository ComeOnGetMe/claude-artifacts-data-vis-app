/**
 * API client for communicating with the FastAPI backend
 */
import type { StreamEvent, StreamCallbacks } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  message: string;
}

/**
 * Process a single SSE event block
 * Backend sends each event as: "event: {type}\ndata: {single JSON object}\n\n"
 * Each data payload is a complete JSON object, not multi-line.
 */
function _processSSEEvent(eventBlock: string, callbacks: StreamCallbacks): void {
  let eventType = 'message'; // default
  let data = '';

  const lines = eventBlock.split('\n');
  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.slice(7).trim();
    } else if (line.startsWith('data: ')) {
      // Backend sends single-line JSON, so we only need the first data line
      // (though SSE spec allows multiple data lines, backend doesn't use them)
      data = line.slice(6).trim();
      break; // Backend sends single data line per event, so we can break after first one
    } else if (line.trim() && !line.startsWith(':')) {
      // Ignore comments (lines starting with :) but log unexpected lines
      console.warn('Unexpected SSE line:', line);
    }
  }

  if (!data) {
    return; // Skip empty events
  }

  try {
    const parsedData: StreamEvent = JSON.parse(data);

    // Validate that parsedData has the expected structure
    if (!parsedData || typeof parsedData !== 'object' || !parsedData.type) {
      throw new Error('Invalid event structure: missing type field');
    }

    // Route to appropriate callback based on event type
    switch (parsedData.type) {
      case 'thought':
        if ('content' in parsedData && typeof parsedData.content === 'string') {
          callbacks.onThought?.(parsedData.content);
        } else {
          throw new Error('Invalid thought event: missing content');
        }
        break;
      case 'code':
        // Code events contain complete UI code (not chunks)
        // Backend accumulates and sends complete code blocks
        if ('content' in parsedData && typeof parsedData.content === 'string') {
          callbacks.onCodeChunk?.(parsedData.content);
        } else {
          throw new Error('Invalid code event: missing content');
        }
        break;
      case 'data':
        if ('payload' in parsedData && parsedData.payload) {
          callbacks.onData?.(parsedData.payload);
        } else {
          throw new Error('Invalid data event: missing payload');
        }
        break;
      case 'error':
        callbacks.onError?.(parsedData);
        break;
      default:
        // TypeScript doesn't know this can happen, but we handle it defensively
        const unknownType = (parsedData as { type: string }).type;
        console.warn('Unknown event type:', unknownType);
    }
  } catch (parseError) {
    // If JSON parsing fails, provide detailed error information
    const errorMessage = parseError instanceof Error ? parseError.message : String(parseError);
    console.error('Failed to parse SSE event as JSON:', {
      error: errorMessage,
      dataPreview: data.substring(0, 200),
      dataLength: data.length,
    });
    
    // Call error callback with parsing error
    callbacks.onError?.({
      type: 'error',
      message: `JSON parse error: ${errorMessage}. Data length: ${data.length}`,
    });
  }
}

/**
 * Process remaining buffer content (for final incomplete events)
 */
function _processSSEBuffer(buffer: string, callbacks: StreamCallbacks): void {
  if (!buffer.trim()) return;
  
  // Try to process as complete event
  try {
    _processSSEEvent(buffer, callbacks);
  } catch (error) {
    // If it fails, it might be incomplete - log but don't error
    console.warn('Buffer contains incomplete event:', error);
  }
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
          // Process any remaining data in buffer
          if (buffer.trim()) {
            try {
              _processSSEBuffer(buffer, callbacks);
            } catch (error) {
              callbacks.onError?.({
                type: 'error',
                message: `Failed to process final buffer: ${error instanceof Error ? error.message : String(error)}`,
              });
            }
          }
          callbacks.onStreamComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE format: "event: <type>\ndata: <json>\n\n"
        // Split on double newlines to get complete events
        const events = buffer.split('\n\n');
        // Keep the last potentially incomplete event in the buffer
        buffer = events.pop() || '';

        for (const eventBlock of events) {
          if (!eventBlock.trim()) continue;
          
          try {
            _processSSEEvent(eventBlock, callbacks);
          } catch (error) {
            console.error('Error processing SSE event:', error);
            callbacks.onError?.({
              type: 'error',
              message: `Failed to process SSE event: ${error instanceof Error ? error.message : String(error)}`,
            });
          }
        }
      }
    } catch (streamError) {
      console.error('Stream reading error:', streamError);
      callbacks.onError?.({
        type: 'error',
        message: `Stream error: ${streamError instanceof Error ? streamError.message : String(streamError)}`,
      });
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

