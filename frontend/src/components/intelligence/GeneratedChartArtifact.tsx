import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import type { ViChartOutput } from '@/types';

type ThemeMode = 'light' | 'dark';

type SeriesDefinition = {
  key: string;
  label: string;
  color: string;
  fill?: boolean;
};

type GeneratedChartArtifactProps = {
  chart: ViChartOutput;
  theme?: ThemeMode;
  showActions?: boolean;
  className?: string;
};

const CHART_SWATCH = ['#06b6d4', '#22c55e', '#6366f1', '#f59e0b', '#ef4444', '#a855f7', '#14b8a6', '#f97316'];

function normalizeChartType(rawType?: string): 'line' | 'bar' | 'pie' | 'unsupported' {
  const value = String(rawType || '').toLowerCase();
  if (value === 'line' || value === 'area') return 'line';
  if (value === 'bar' || value === 'horizontalbar') return 'bar';
  if (value === 'pie' || value === 'doughnut') return 'pie';
  return 'unsupported';
}

function normalizeColor(color: unknown, index: number): string {
  if (typeof color === 'string' && color.trim()) return color;
  if (Array.isArray(color)) {
    const firstString = color.find((item) => typeof item === 'string' && item.trim());
    if (typeof firstString === 'string') return firstString;
  }
  return CHART_SWATCH[index % CHART_SWATCH.length];
}

function normalizeNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function buildCartesianData(chart: ViChartOutput): { rows: Array<Record<string, string | number | null>>; series: SeriesDefinition[] } | null {
  const rawLabels = Array.isArray(chart.config?.data?.labels) ? chart.config.data.labels : [];
  const rawDatasets = Array.isArray(chart.config?.data?.datasets) ? chart.config.data.datasets : [];

  if (!rawLabels.length || !rawDatasets.length) return null;

  const labels = rawLabels.map((label: unknown, index: number) => {
    if (label == null || label === '') return `Point ${index + 1}`;
    return String(label);
  });

  const series = rawDatasets.map((dataset: Record<string, unknown>, index: number) => {
    const label = typeof dataset.label === 'string' && dataset.label.trim() ? dataset.label : `Series ${index + 1}`;
    return {
      key: `${label}_${index}`,
      label,
      color: normalizeColor(dataset.borderColor ?? dataset.backgroundColor, index),
      fill: Boolean(dataset.fill),
    };
  });

  const rows = labels.map((label: string, labelIndex: number) => {
    const row: Record<string, string | number | null> = { label };
    rawDatasets.forEach((dataset: Record<string, unknown>, datasetIndex: number) => {
      const values = Array.isArray(dataset.data) ? dataset.data : [];
      row[series[datasetIndex].key] = normalizeNumber(values[labelIndex]);
    });
    return row;
  });

  const hasNumericValue = rows.some((row: Record<string, string | number | null>) =>
    series.some((item: SeriesDefinition) => typeof row[item.key] === 'number'),
  );
  return hasNumericValue ? { rows, series } : null;
}

function buildPieData(chart: ViChartOutput): Array<{ name: string; value: number; color: string }> | null {
  const rawLabels = Array.isArray(chart.config?.data?.labels) ? chart.config.data.labels : [];
  const rawDatasets = Array.isArray(chart.config?.data?.datasets) ? chart.config.data.datasets : [];
  const firstDataset = rawDatasets[0];
  const values = Array.isArray(firstDataset?.data) ? firstDataset.data : [];

  if (!rawLabels.length || !values.length) return null;

  const rows = rawLabels
    .map((label: unknown, index: number) => ({
      name: label == null || label === '' ? `Slice ${index + 1}` : String(label),
      value: normalizeNumber(values[index]),
      color: Array.isArray(firstDataset?.backgroundColor)
        ? normalizeColor(firstDataset.backgroundColor[index], index)
        : normalizeColor(firstDataset?.backgroundColor, index),
    }))
    .filter((item: { name: string; value: number | null; color: string }): item is { name: string; value: number; color: string } => typeof item.value === 'number');

  return rows.length ? rows : null;
}

function fallbackPanel(chart: ViChartOutput, theme: ThemeMode) {
  const shellClass = theme === 'dark'
    ? 'border-slate-700/50 bg-slate-900/40 text-slate-300'
    : 'border-slate-200 bg-slate-50 text-slate-600';
  const imageClass = theme === 'dark' ? 'bg-slate-950/40' : 'bg-slate-50';
  const copyClass = theme === 'dark' ? 'text-slate-400' : 'text-slate-500';

  if (chart.chart_url) {
    return (
      <div className={`rounded-2xl border ${shellClass} overflow-hidden`}>
        <div className={`p-3 ${imageClass}`}>
          <img src={chart.chart_url} alt={chart.title} className="w-full rounded" loading="lazy" />
        </div>
        <div className={`px-4 pb-4 text-xs ${copyClass}`}>
          Rendered from external chart image because the returned chart type is not supported locally.
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl border ${shellClass} p-4 text-sm`}>
      Chart configuration was returned, but there was not enough data to render it.
    </div>
  );
}

export function GeneratedChartArtifact({
  chart,
  theme = 'light',
  showActions = false,
  className = '',
}: GeneratedChartArtifactProps) {
  const normalizedType = normalizeChartType(chart.chart_type);
  const shellClass = theme === 'dark'
    ? 'border-slate-700/50 bg-slate-800/50'
    : 'border-slate-200 bg-white shadow-[0_8px_22px_rgba(15,23,42,0.05)]';
  const borderClass = theme === 'dark' ? 'border-slate-700/50' : 'border-slate-200';
  const titleClass = theme === 'dark' ? 'text-slate-200' : 'text-slate-700';
  const mutedClass = theme === 'dark' ? 'text-slate-400' : 'text-slate-500';
  const insightShellClass = theme === 'dark'
    ? 'border-cyan-500/20 bg-cyan-500/10 text-cyan-300'
    : 'border-slate-200 bg-slate-50 text-slate-600';
  const actionClass = theme === 'dark'
    ? 'border-slate-700 bg-slate-900/60 text-slate-300 hover:border-slate-600 hover:text-white'
    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900';

  const cartesian = normalizedType !== 'pie' ? buildCartesianData(chart) : null;
  const pieData = normalizedType === 'pie' ? buildPieData(chart) : null;
  const canRenderLocally = Boolean((normalizedType === 'pie' && pieData) || (normalizedType !== 'pie' && cartesian));
  const tooltipStyle = theme === 'dark'
    ? { backgroundColor: '#020617', border: '1px solid #334155', color: '#e2e8f0' }
    : { backgroundColor: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a' };

  return (
    <div className={`overflow-hidden rounded-2xl border ${shellClass} ${className}`.trim()}>
      <div className={`flex items-center justify-between border-b px-4 py-2.5 ${borderClass}`}>
        <div className={`text-xs font-medium ${titleClass}`}>{chart.title}</div>
        <div className={`text-[11px] uppercase tracking-[0.12em] ${mutedClass}`}>{chart.chart_type}</div>
      </div>

      <div className="p-4">
        {canRenderLocally ? (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {normalizedType === 'bar' && cartesian ? (
                <BarChart data={cartesian.rows} margin={{ top: 8, right: 12, left: 0, bottom: 12 }}>
                  <CartesianGrid stroke={theme === 'dark' ? '#334155' : '#e2e8f0'} strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: theme === 'dark' ? '#94a3b8' : '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: theme === 'dark' ? '#94a3b8' : '#64748b' }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  {cartesian.series.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
                  {cartesian.series.map((series) => (
                    <Bar key={series.key} dataKey={series.key} name={series.label} fill={series.color} radius={[6, 6, 0, 0]} />
                  ))}
                </BarChart>
              ) : normalizedType === 'line' && cartesian ? (
                <LineChart data={cartesian.rows} margin={{ top: 8, right: 12, left: 0, bottom: 12 }}>
                  <CartesianGrid stroke={theme === 'dark' ? '#334155' : '#e2e8f0'} strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: theme === 'dark' ? '#94a3b8' : '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: theme === 'dark' ? '#94a3b8' : '#64748b' }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  {cartesian.series.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
                  {cartesian.series.map((series) => (
                    <Line
                      key={series.key}
                      type="monotone"
                      dataKey={series.key}
                      name={series.label}
                      stroke={series.color}
                      strokeWidth={3}
                      dot={{ r: 3 }}
                      fill={series.color}
                    />
                  ))}
                </LineChart>
              ) : normalizedType === 'pie' && pieData ? (
                <PieChart>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={96} label>
                    {pieData.map((entry, index) => (
                      <Cell key={`${entry.name}_${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              ) : (
                <></>
              )}
            </ResponsiveContainer>
          </div>
        ) : (
          fallbackPanel(chart, theme)
        )}
      </div>

      <div className={`px-4 pb-4 text-xs ${mutedClass}`}>
        {canRenderLocally ? 'Rendered locally from the AI response payload for reliable in-app display.' : 'Using fallback chart rendering path.'}
      </div>

      {chart.insight && (
        <div className="px-4 pb-3">
          <div className={`rounded-lg border p-3 text-sm ${insightShellClass}`}>
            {chart.insight}
          </div>
        </div>
      )}

      <div className={`px-4 pb-4 text-xs ${mutedClass}`}>{chart.data_summary}</div>

      {showActions && chart.chart_url && (
        <div className="flex gap-2 px-4 pb-4">
          <a
            href={chart.chart_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs transition-all border ${actionClass}`}
          >
            Open Full Size
          </a>
          <a
            href={chart.chart_url}
            download
            className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs transition-all border ${actionClass}`}
          >
            Download
          </a>
        </div>
      )}
    </div>
  );
}
