'use client';

import React from 'react';
import { Runner } from 'react-runner';
import { ErrorBoundary } from './ErrorBoundary';
import type { QueryResult } from '@/lib/types';
import * as Recharts from 'recharts';

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

  // Transform QueryResult format (columns + rows) to Recharts format (array of objects)
  let transformedData: any[] | null = null;
  if (data && data.columns && data.rows) {
    transformedData = data.rows.map((row) => {
      const obj: Record<string, any> = {};
      data.columns.forEach((col, index) => {
        obj[col] = row[index];
      });
      return obj;
    });
  }

  // Strip import statements from the code since react-runner doesn't handle them
  // react-runner needs all dependencies in scope, not as imports
  let processedCode = code;
  
  // Remove import statements (handle both single-line and multiline)
  // Match import statements more comprehensively
  processedCode = processedCode.replace(/import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+)?['"]react['"];?\s*/g, '');
  processedCode = processedCode.replace(/import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+)?['"]recharts['"];?\s*/g, '');
  processedCode = processedCode.replace(/import\s+.*?from\s+['"]@\/components\/ui\/.*?['"];?\s*/g, '');
  
  // Clean up any extra blank lines left by removed imports
  processedCode = processedCode.replace(/\n{3,}/g, '\n\n').trim();

  // Wrap the component code to pass data as a prop
  // The backend generates: export default function Component({ data })
  // react-runner renders the default export, so we wrap it to pass the data prop
  let wrappedCode = processedCode;
  
  // If the code exports a default function that expects { data } prop,
  // wrap it to pass the data from scope
  if (processedCode.includes('export default function')) {
    // Extract component name
    const nameMatch = processedCode.match(/export default function (\w+)/);
    if (nameMatch) {
      const componentName = nameMatch[1];
      // Replace export default with just the function definition
      const functionCode = processedCode.replace(/export default /, '');
      // Use JSX syntax for wrapping (react-runner handles JSX)
      wrappedCode = `
${functionCode}

// Wrap to pass data prop
const WrappedComponent = () => {
  return <${componentName} data={transformedData || null} />;
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
          {transformedData ? `Rendering with ${transformedData.length} data points` : 'Rendering without data'}
        </p>
      </div>
      
      <ErrorBoundary>
        <div className="border border-gray-200 rounded-lg p-4 bg-white" style={{ minHeight: '500px' }}>
          <Runner
            code={wrappedCode}
            scope={{
              React,
              // Make all Recharts components available in scope
              ResponsiveContainer: Recharts.ResponsiveContainer,
              BarChart: Recharts.BarChart,
              Bar: Recharts.Bar,
              XAxis: Recharts.XAxis,
              YAxis: Recharts.YAxis,
              Tooltip: Recharts.Tooltip,
              CartesianGrid: Recharts.CartesianGrid,
              LineChart: Recharts.LineChart,
              Line: Recharts.Line,
              PieChart: Recharts.PieChart,
              Pie: Recharts.Pie,
              AreaChart: Recharts.AreaChart,
              Area: Recharts.Area,
              ScatterChart: Recharts.ScatterChart,
              ComposedChart: Recharts.ComposedChart,
              Cell: Recharts.Cell,
              Legend: Recharts.Legend,
              // Also provide the namespace for any other components
              recharts: Recharts,
              data: transformedData || null,
              transformedData: transformedData || null,
            }}
          />
        </div>
      </ErrorBoundary>
    </div>
  );
}

