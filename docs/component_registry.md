# Component Registry
This file lists the only allowed libraries and components for the Agent to use when generating Dynamic UI Artifacts. The Agent must not attempt to use any library not listed here.

## 1. Core Visualization (Recharts)
All charts should be responsive using <ResponsiveContainer />.

Charts: LineChart, BarChart, PieChart, AreaChart, ScatterChart, ComposedChart.

Elements: XAxis, YAxis, CartesianGrid, Tooltip, Legend, Bar, Line, Area, Cell.

## 2. UI Components (Shadcn UI)

The following pre-installed components are available. Use them for layout and data presentation:

Data Display: Table.

Feedback: Alert, Progress, Skeleton.

Input (for Parameterization): Button, Slider, Switch, Tabs.

## 3. Icons (Lucide React)

Standard icons for UI context (e.g., TrendingUp, AlertCircle, Database, Download).

## 4. Styling (Tailwind CSS)

Use standard Tailwind utility classes.

Theme: Respect dark and light mode variables (e.g., bg-background, text-foreground).

Colors: Use the theme-safe palette (e.g., primary, secondary, muted, accent).

## 5. Implementation Standard (The "Contract")

When generating a component, the Agent must follow this exact template:

```TypeScript

import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

/**
 * @param {Array} data - The dataset returned from the Python backend
 * @param {Object} params - User-defined parameters for customization
 */
export default function GeneratedViz({ data, params }) {
  if (!data || data.length === 0) {
    return <div className="p-4 text-center">No data available to visualize.</div>;
  }

  return (
    <div className="w-full h-full p-4">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">{params?.title || 'Data Visualization'}</h2>
      </div>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            {/* Viz Logic Here */}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

## 6. Prohibited Practices

No External API Calls: The generated component must not fetch data itself. It must rely on the passed data prop.

No LocalStorage: Do not attempt to persist state inside the generated component.

No Framer Motion: Unless explicitly requested, stick to CSS transitions and Recharts animations to keep the bundle light.
