'use client';

import type { QueryResult } from '@/lib/types';

interface DataTableProps {
  data: QueryResult;
}

export default function DataTable({ data }: DataTableProps) {
  const { columns, rows, row_count } = data;

  return (
    <div className="overflow-x-auto border border-gray-300 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column, index) => (
              <th
                key={index}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-50">
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                >
                  {cell ?? <span className="text-gray-400">null</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="bg-gray-50 px-6 py-2 text-xs text-gray-500">
        {row_count} row{row_count !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

