'use client';

import { useState, useRef, useEffect } from 'react';
import { streamChat } from '@/lib/api';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamContent, setCurrentStreamContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamContent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isStreaming) {
      return;
    }

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setCurrentStreamContent('');

    // Use a ref to track the accumulated content
    let accumulatedContent = '';

    await streamChat(
      userMessage.content,
      (chunk) => {
        accumulatedContent += chunk;
        setCurrentStreamContent(accumulatedContent);
      },
      () => {
        // Stream complete - add final message
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: accumulatedContent,
            timestamp: new Date(),
          },
        ]);
        setCurrentStreamContent('');
        setIsStreaming(false);
      },
      (error) => {
        console.error('Stream error:', error);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${error.message}`,
            timestamp: new Date(),
          },
        ]);
        setCurrentStreamContent('');
        setIsStreaming(false);
      }
    );
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
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
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs mt-1 opacity-70">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isStreaming && currentStreamContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg p-3 bg-gray-200 text-gray-900">
              <p className="whitespace-pre-wrap">{currentStreamContent}</p>
              <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse ml-1" />
            </div>
          </div>
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

