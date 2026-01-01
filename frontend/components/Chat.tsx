'use client';

import { useState, useRef, useEffect } from 'react';
import { streamChat } from '@/lib/api';
import type { QueryResult } from '@/lib/types';
import DataTable from './DataTable';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type?: 'text' | 'data' | 'code';
  data?: QueryResult;
  code?: string;
}

interface ChatProps {
  onCodeUpdate?: (code: string | null) => void;
  onDataUpdate?: (data: QueryResult | null) => void;
}

export default function Chat({ onCodeUpdate, onDataUpdate }: ChatProps = {}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThought, setCurrentThought] = useState('');
  const [currentCodeChunks, setCurrentCodeChunks] = useState('');
  const [currentData, setCurrentData] = useState<QueryResult | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const accumulatedThoughtRef = useRef('');
  const accumulatedCodeRef = useRef('');

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentThought, currentCodeChunks, currentData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isStreaming) {
      return;
    }

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
      type: 'text',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setCurrentThought('');
    setCurrentCodeChunks('');
    setCurrentData(null);
    accumulatedThoughtRef.current = '';
    accumulatedCodeRef.current = '';
    // Clear preview when starting new request
    onCodeUpdate?.(null);
    onDataUpdate?.(null);

    await streamChat(userMessage.content, {
      onThought: (content) => {
        accumulatedThoughtRef.current = content;
        setCurrentThought(content);
      },
      onCodeChunk: (chunk) => {
        accumulatedCodeRef.current += chunk;
        setCurrentCodeChunks(accumulatedCodeRef.current);
        // Update preview with latest code
        onCodeUpdate?.(accumulatedCodeRef.current);
      },
      onData: (payload) => {
        setCurrentData(payload);
        // Update preview with latest data
        onDataUpdate?.(payload);
        // Add data message immediately
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Data received',
            timestamp: new Date(),
            type: 'data',
            data: payload,
          },
        ]);
        setCurrentData(null);
      },
      onError: (error) => {
        console.error('Stream error:', error);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${error.message}`,
            timestamp: new Date(),
            type: 'text',
          },
        ]);
        setIsStreaming(false);
        setCurrentThought('');
        setCurrentCodeChunks('');
        setCurrentData(null);
        accumulatedThoughtRef.current = '';
        accumulatedCodeRef.current = '';
        // Clear preview on error
        onCodeUpdate?.(null);
        onDataUpdate?.(null);
      },
      onStreamComplete: () => {
        // Add final messages for thought and code if they exist
        const newMessages: Message[] = [];
        
        if (accumulatedThoughtRef.current) {
          newMessages.push({
            role: 'assistant',
            content: accumulatedThoughtRef.current,
            timestamp: new Date(),
            type: 'text',
          });
        }
        
        if (accumulatedCodeRef.current) {
          newMessages.push({
            role: 'assistant',
            content: `Code received (${accumulatedCodeRef.current.length} characters)`,
            timestamp: new Date(),
            type: 'code',
            code: accumulatedCodeRef.current,
          });
          // Ensure preview has final code
          onCodeUpdate?.(accumulatedCodeRef.current);
        }
        
        if (newMessages.length > 0) {
          setMessages((prev) => [...prev, ...newMessages]);
        }
        
        setCurrentThought('');
        setCurrentCodeChunks('');
        setCurrentData(null);
        accumulatedThoughtRef.current = '';
        accumulatedCodeRef.current = '';
        setIsStreaming(false);
      },
    });
  };

  return (
    <div className="flex flex-col h-full p-4">
      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-900'
              }`}
            >
              {message.type === 'data' && message.data ? (
                <div>
                  <p className="text-sm font-semibold mb-2">Data Table:</p>
                  <DataTable data={message.data} />
                </div>
              ) : message.type === 'code' && message.code ? (
                <div>
                  <p className="text-sm font-semibold mb-2">Code Received:</p>
                  <p className="text-xs text-gray-600 mb-2">
                    {message.code.length} characters
                  </p>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-xs overflow-x-auto">
                    <code>{message.code}</code>
                  </pre>
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{message.content}</p>
              )}
              <p className="text-xs mt-1 opacity-70">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {/* Streaming indicators */}
        {isStreaming && (
          <>
            {currentThought && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg p-3 bg-gray-200 text-gray-900">
                  <p className="whitespace-pre-wrap">{currentThought}</p>
                  <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse ml-1" />
                </div>
              </div>
            )}
            {currentCodeChunks && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg p-3 bg-gray-200 text-gray-900">
                  <p className="text-sm font-semibold mb-2">Receiving code...</p>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-xs overflow-x-auto">
                    <code>{currentCodeChunks}</code>
                  </pre>
                  <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse ml-1" />
                </div>
              </div>
            )}
            {currentData && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg p-3 bg-gray-200 text-gray-900">
                  <p className="text-sm font-semibold mb-2">Loading data...</p>
                  <DataTable data={currentData} />
                </div>
              </div>
            )}
          </>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isStreaming}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

