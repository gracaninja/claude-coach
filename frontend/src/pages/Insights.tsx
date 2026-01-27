import { useQuery } from '@tanstack/react-query'
import { fetchInsights, fetchUserComparison, downloadMetricsJson, Insight } from '../api/community'

const severityColors: Record<string, string> = {
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  suggestion: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  warning: 'bg-red-50 border-red-200 text-red-800',
}

const categoryIcons: Record<string, string> = {
  efficiency: '⚡',
  tools: '🔧',
  errors: '⚠️',
  patterns: '📊',
}

function InsightCard({ insight }: { insight: Insight }) {
  return (
    <div className={`p-4 rounded-lg border ${severityColors[insight.severity] || severityColors.info}`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{categoryIcons[insight.category] || '💡'}</span>
        <div className="flex-1">
          <h3 className="font-semibold">{insight.title}</h3>
          <p className="text-sm mt-1">{insight.description}</p>
          {insight.metric_value !== undefined && (
            <div className="mt-2 text-sm">
              <span className="font-medium">{insight.metric_label}:</span>{' '}
              <span>{typeof insight.metric_value === 'number' ? insight.metric_value.toFixed(1) : insight.metric_value}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function PercentileBar({ label, value, description }: { label: string; value: number; description: string }) {
  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium">{label}</span>
        <span>{value}th percentile</span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all"
          style={{ width: `${value}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">{description}</p>
    </div>
  )
}

function Insights() {
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['insights'],
    queryFn: fetchInsights,
  })

  const { data: comparison, isLoading: comparisonLoading } = useQuery({
    queryKey: ['userComparison'],
    queryFn: () => fetchUserComparison(30),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Insights & Community</h1>
        <button
          onClick={downloadMetricsJson}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          Export Metrics
        </button>
      </div>

      {/* Community Comparison */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">How You Compare</h2>
        {comparisonLoading ? (
          <p>Loading comparison...</p>
        ) : comparison ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <PercentileBar
                label="Session Activity"
                value={comparison.sessions_percentile}
                description={`${comparison.user_sessions_per_day.toFixed(1)} sessions/day vs ${comparison.benchmark.avg_sessions_per_day.toFixed(1)} avg`}
              />
              <PercentileBar
                label="Token Usage"
                value={comparison.tokens_percentile}
                description={`${Math.round(comparison.user_tokens_per_session).toLocaleString()} tokens/session vs ${comparison.benchmark.tokens_p50.toLocaleString()} median`}
              />
              <PercentileBar
                label="Cache Efficiency"
                value={comparison.efficiency_percentile}
                description={`${(comparison.user_cache_hit_rate * 100).toFixed(0)}% cache hit rate`}
              />
            </div>
            <div>
              <h3 className="font-medium mb-3">Community Insights</h3>
              {comparison.insights.length > 0 ? (
                <ul className="space-y-2">
                  {comparison.insights.map((insight, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-indigo-500">•</span>
                      {insight}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 text-sm">You're performing at community average!</p>
              )}

              <div className="mt-4 p-3 bg-gray-50 rounded">
                <h4 className="text-sm font-medium mb-2">Community Stats</h4>
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                  <div>Users: {comparison.benchmark.total_users.toLocaleString()}</div>
                  <div>Period: {comparison.benchmark.data_period_days} days</div>
                  <div>Avg Tools: {comparison.benchmark.avg_tools_per_session.toFixed(1)}/session</div>
                  <div>Error Rate: {(comparison.benchmark.avg_error_rate * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">No data available</p>
        )}
      </div>

      {/* Personal Insights */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Personal Insights</h2>
        {insightsLoading ? (
          <p>Loading insights...</p>
        ) : insights && insights.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.map((insight, idx) => (
              <InsightCard key={idx} insight={insight} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500">
            No insights yet. Import more sessions to see personalized recommendations.
          </p>
        )}
      </div>

      {/* Most Used Tools in Community */}
      {comparison && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Most Popular Tools in Community</h2>
          <div className="flex flex-wrap gap-2">
            {comparison.benchmark.most_used_tools.map((tool, idx) => (
              <span
                key={tool}
                className={`px-3 py-1 rounded-full text-sm ${
                  idx < 3 ? 'bg-indigo-100 text-indigo-800' : 'bg-gray-100 text-gray-700'
                }`}
              >
                {idx < 3 && <span className="mr-1">#{idx + 1}</span>}
                {tool}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Insights
