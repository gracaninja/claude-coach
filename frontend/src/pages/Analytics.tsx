import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { fetchTokenUsage, fetchToolUsage, fetchErrorStats, fetchPlanModeStats } from '../api/analytics'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function Analytics() {
  const { data: tokenData, isLoading: tokenLoading } = useQuery({
    queryKey: ['tokenUsage'],
    queryFn: fetchTokenUsage,
  })

  const { data: toolData, isLoading: toolLoading } = useQuery({
    queryKey: ['toolUsage'],
    queryFn: fetchToolUsage,
  })

  const { data: errorData, isLoading: errorLoading } = useQuery({
    queryKey: ['errorStats'],
    queryFn: fetchErrorStats,
  })

  const { data: planModeData, isLoading: planModeLoading } = useQuery({
    queryKey: ['planModeStats'],
    queryFn: fetchPlanModeStats,
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Token Usage Over Time</h2>
          {tokenLoading ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={tokenData?.data ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="input_tokens" stroke="#6366f1" name="Input" />
                <Line type="monotone" dataKey="output_tokens" stroke="#22c55e" name="Output" />
                <Line type="monotone" dataKey="cache_read_tokens" stroke="#f59e0b" name="Cache Read" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Tool Usage Distribution</h2>
          {toolLoading ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={toolData?.data?.slice(0, 6) ?? []}
                  dataKey="count"
                  nameKey="tool_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => entry.tool_name}
                >
                  {toolData?.data?.slice(0, 6).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Tool Usage (Top 15)</h2>
          {toolLoading ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={toolData?.data?.slice(0, 15) ?? []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="tool_name" type="category" width={100} fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Error Types</h2>
          {errorLoading ? (
            <p>Loading...</p>
          ) : errorData?.data?.length === 0 ? (
            <p className="text-gray-500">No errors recorded</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={errorData?.data ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="error_type" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Total Input Tokens</h3>
            <p className="text-xl font-bold">{tokenData?.total_input_tokens?.toLocaleString() ?? '-'}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Total Output Tokens</h3>
            <p className="text-xl font-bold">{tokenData?.total_output_tokens?.toLocaleString() ?? '-'}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Total Tool Calls</h3>
            <p className="text-xl font-bold">{toolData?.total_tool_calls?.toLocaleString() ?? '-'}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Total Errors</h3>
            <p className="text-xl font-bold">{errorData?.total_errors?.toLocaleString() ?? '-'}</p>
          </div>
        </div>
      </div>

      {/* Planning vs Execution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Planning vs Execution</h2>
        {planModeLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="space-y-6">
            {/* Time comparison */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Time Distribution</h3>
              <div className="flex h-8 rounded-lg overflow-hidden">
                {(planModeData?.aggregate.total_planning_time_seconds ?? 0) > 0 && (
                  <div
                    className="bg-indigo-500 flex items-center justify-center text-white text-sm"
                    style={{
                      width: `${planModeData?.aggregate.avg_planning_percentage ?? 0}%`,
                      minWidth: '50px',
                    }}
                  >
                    Planning
                  </div>
                )}
                <div
                  className="bg-green-500 flex items-center justify-center text-white text-sm flex-1"
                >
                  Execution
                </div>
              </div>
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>
                  Planning: {formatTime(planModeData?.aggregate.total_planning_time_seconds ?? 0)}
                </span>
                <span>
                  Execution: {formatTime(planModeData?.aggregate.total_execution_time_seconds ?? 0)}
                </span>
              </div>
            </div>

            {/* Token comparison */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Planning Tokens</h3>
                <p className="text-xl font-bold text-indigo-600">
                  {planModeData?.aggregate.total_planning_tokens?.toLocaleString() ?? '0'}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Execution Tokens</h3>
                <p className="text-xl font-bold text-green-600">
                  {planModeData?.aggregate.total_execution_tokens?.toLocaleString() ?? '0'}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Planning Messages</h3>
                <p className="text-xl font-bold text-indigo-600">
                  {planModeData?.aggregate.total_planning_messages?.toLocaleString() ?? '0'}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Execution Messages</h3>
                <p className="text-xl font-bold text-green-600">
                  {planModeData?.aggregate.total_execution_messages?.toLocaleString() ?? '0'}
                </p>
              </div>
            </div>

            {/* Sessions with planning */}
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-500">
                Sessions with planning: {planModeData?.aggregate.sessions_with_planning ?? 0} / {planModeData?.aggregate.total_sessions ?? 0}
              </span>
              <span className="text-gray-500">
                Total plan mode entries: {planModeData?.aggregate.total_plan_mode_entries ?? 0}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

export default Analytics
