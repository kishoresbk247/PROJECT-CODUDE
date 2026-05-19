/**
 * ComplexityChart.jsx — Bar chart of per-function complexity scores
 *
 * Uses recharts to plot complexity_scores per function.
 *
 * Props:
 *   data — array of { function_name, time_complexity, space_complexity, score }
 */

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

function getBarColor(score) {
  if (score >= 8) return '#22c55e';
  if (score >= 5) return '#f59e0b';
  return '#ef4444';
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: 'rgba(17,24,39,0.95)',
      border: '1px solid rgba(99,102,241,0.3)',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 13,
      color: '#f1f5f9',
      backdropFilter: 'blur(8px)',
    }}>
      <p style={{ fontWeight: 700, marginBottom: 4 }}>{d.function_name}</p>
      <p>Time: <span style={{ color: '#a78bfa' }}>{d.time_complexity}</span></p>
      <p>Space: <span style={{ color: '#a78bfa' }}>{d.space_complexity}</span></p>
      <p>Score: <span style={{ color: getBarColor(d.score), fontWeight: 700 }}>{d.score}/10</span></p>
    </div>
  );
}

export default function ComplexityChart({ data = [] }) {
  if (!data.length) return null;

  return (
    <div className="complexity-chart" id="complexity-chart">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 4 }}>
          <XAxis
            dataKey="function_name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#2a3040' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 10]}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#2a3040' }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.06)' }} />
          <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={48}>
            {data.map((entry, i) => (
              <Cell key={i} fill={getBarColor(entry.score)} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
