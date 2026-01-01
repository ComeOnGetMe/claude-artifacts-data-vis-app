'use client';

import React from 'react';
import { Runner } from 'react-runner';
import { ErrorBoundary } from './ErrorBoundary';
import type { QueryResult } from '@/lib/types';

interface PreviewProps {
  code: string | null;
  data?: QueryResult | null;
}

export default function Preview({ code, data }: PreviewProps) {
  if (!code) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-lg mb-2">No code to preview</p>
          <p className="text-sm">Code will appear here when generated</p>
        </div>
      </div>
    );
  }

  // Wrap the component code to pass data as a prop
  // The backend generates: export default function Component({ data })
  // react-runner renders the default export, so we wrap it to pass the data prop
  let wrappedCode = code;
  
  // If the code exports a default function that expects { data } prop,
  // wrap it to pass the data from scope
  if (code.includes('export default function') && code.includes('{ data }')) {
    // Extract component name using a simpler regex (just get the name)
    const nameMatch = code.match(/export default function (\w+)/);
    if (nameMatch) {
      const componentName = nameMatch[1];
      // Replace export default with just the function definition
      const functionCode = code.replace(/export default /, '');
      wrappedCode = `
${functionCode}

// Wrap to pass data prop
const WrappedComponent = () => {
  return React.createElement(${componentName}, { data: data || null });
};

export default WrappedComponent;
`;
    }
  }

  return (
    <div className="h-full overflow-auto p-4">
      <div className="mb-4 pb-4 border-b">
        <h2 className="text-xl font-bold mb-2">Preview</h2>
        <p className="text-sm text-gray-600">
          {data ? 'Rendering with data' : 'Rendering without data'}
        </p>
      </div>
      
      <ErrorBoundary>
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <Runner
            code={wrappedCode}
            scope={{
              React,
              data: data || null,
            }}
          />
        </div>
      </ErrorBoundary>
    </div>
  );
}

