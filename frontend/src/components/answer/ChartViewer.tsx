"use client";

import type { ChartSpec } from "@/lib/types";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

interface ChartViewerProps {
  spec: ChartSpec;
}

const CHART_COLORS = [
  "hsl(217, 91%, 60%)",
  "hsl(160, 60%, 45%)",
  "hsl(38, 92%, 50%)",
  "hsl(0, 72%, 51%)",
  "hsl(280, 65%, 60%)",
  "hsl(190, 80%, 45%)",
  "hsl(330, 70%, 55%)",
  "hsl(60, 70%, 50%)",
];

const tooltipStyle = {
  contentStyle: {
    background: "hsl(224, 71%, 4%)",
    border: "1px solid hsl(216, 34%, 17%)",
    borderRadius: "0.5rem",
    fontSize: "0.75rem",
    color: "hsl(213, 31%, 91%)",
  },
};

export function ChartViewer({ spec }: ChartViewerProps) {
  const { chart_type, title, x_field, y_field, data } = spec;

  if (!data || data.length === 0) return null;

  const renderChart = () => {
    switch (chart_type) {
      case "bar":
      case "histogram":
      case "stacked_bar":
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(216, 34%, 17%)" />
            <XAxis
              dataKey={x_field}
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
            />
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar
              dataKey={y_field}
              fill={CHART_COLORS[0]}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        );

      case "line":
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(216, 34%, 17%)" />
            <XAxis
              dataKey={x_field}
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
            />
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey={y_field}
              stroke={CHART_COLORS[0]}
              strokeWidth={2}
              dot={{ fill: CHART_COLORS[0], r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        );

      case "area":
        return (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(216, 34%, 17%)" />
            <XAxis
              dataKey={x_field}
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
            />
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area
              type="monotone"
              dataKey={y_field}
              stroke={CHART_COLORS[0]}
              fill={CHART_COLORS[0]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
          </AreaChart>
        );

      case "pie":
        return (
          <PieChart>
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Pie
              data={data}
              dataKey={y_field}
              nameKey={x_field}
              cx="50%"
              cy="50%"
              outerRadius={100}
              innerRadius={50}
              paddingAngle={2}
              strokeWidth={0}
            >
              {data.map((_, idx) => (
                <Cell
                  key={idx}
                  fill={CHART_COLORS[idx % CHART_COLORS.length]}
                />
              ))}
            </Pie>
          </PieChart>
        );

      case "scatter":
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(216, 34%, 17%)" />
            <XAxis
              dataKey={x_field}
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
              name={x_field}
            />
            <YAxis
              dataKey={y_field}
              tick={{ fontSize: 11, fill: "hsl(215, 20%, 55%)" }}
              stroke="hsl(216, 34%, 17%)"
              name={y_field}
            />
            <Tooltip {...tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Scatter name={title} data={data} fill={CHART_COLORS[0]} />
          </ScatterChart>
        );

      default:
        return (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Unsupported chart type: {chart_type}
          </div>
        );
    }
  };

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium">{title}</h4>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
