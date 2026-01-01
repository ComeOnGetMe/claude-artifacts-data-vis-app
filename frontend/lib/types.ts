/**
 * Type definitions for SSE events and data structures
 */

export interface QueryResult {
  columns: string[];
  rows: (string | number)[][];
  row_count: number;
}

export type EventType = 'thought' | 'code' | 'data' | 'error';

export interface ThoughtEvent {
  type: 'thought';
  content: string;
}

export interface CodeEvent {
  type: 'code';
  language: string;
  content: string;
}

export interface DataEvent {
  type: 'data';
  payload: QueryResult;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
  stage?: 'sql_execution' | 'code_generation' | 'data_fetch';
}

export type StreamEvent = ThoughtEvent | CodeEvent | DataEvent | ErrorEvent;

export interface StreamCallbacks {
  onThought?: (content: string) => void;
  onCodeChunk?: (chunk: string) => void;
  onData?: (payload: QueryResult) => void;
  onError?: (error: ErrorEvent) => void;
  onStreamComplete?: () => void;
}

