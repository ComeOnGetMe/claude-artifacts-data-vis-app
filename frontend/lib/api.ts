/**
 * API client for communicating with the FastAPI backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  message: string;
}

/**
 * Stream chat messages from the backend
 * @param message The user's message
 * @param onChunk Callback for each chunk received
 * @param onComplete Callback when stream completes
 * @param onError Callback for errors
 */
export async function streamChat(
  message: string,
  onChunk: (chunk: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void
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

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete?.();
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        // Parse SSE format: "data: <content>\n\n"
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6); // Remove "data: " prefix
            onChunk(content);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error(String(error)));
  }
}

