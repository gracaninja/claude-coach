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
import {
  fetchTokenUsage,
  fetchToolUsage,
  fetchErrorStats,
  fetchPlanModeStats,
  fetchAgentAnalytics,
  fetchSkillAnalytics,
  fetchMcpAnalytics,
} from '../api/analytics'
import { useProjectFilter } from '../context/ProjectContext'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
const AGENT_COLORS = ['#f97316', '#fb923c', '#fdba74', '#fed7aa', '#ffedd5', '#fff7ed']

function formatTokens(n?: number): string {
  if (!n) return '0'
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return n.toString()
}

function formatDuration(ms?: number): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

function Analytics() {
  const { projectsParam } = useProjectFilter()

  const { data: tokenData, isLoading: tokenLoading } = useQuery({
    queryKey: ['tokenUsage', projectsParam],
    queryFn: () => fetchTokenUsage({ project: projectsParam }),
  })

  const { data: toolData, isLoading: toolLoading } = useQuery({
    queryKey: ['toolUsage', projectsParam],
    queryFn: () => fetchToolUsage({ project: projectsParam }),
  })

  const { data: errorData, isLoading: errorLoading } = useQuery({
    queryKey: ['errorStats', projectsParam],
    queryFn: () => fetchErrorStats({ project: projectsParam }),
  })

  const { data: planModeData, isLoading: planModeLoading } = useQuery({
    queryKey: ['planModeStats'],
    queryFn: fetchPlanModeStats,
  })

  const { data: agentData, isLoading: agentLoading } = useQuery({
    queryKey: ['agentAnalytics', projectsParam],
    queryFn: () => fetchAgentAnalytics({ project: projectsParam }),
  })

  const { data: skillData, isLoading: skillLoading } = useQuery({
    queryKey: ['skillAnalytics', projectsParam],
    queryFn: () => fetchSkillAnalytics({ project: projectsParam }),
  })

  const { data: mcpData, isLoading: mcpLoading } = useQuery({
    queryKey: ['mcpAnalytics', projectsParam],
    queryFn: () => fetchMcpAnalytics({ project: projectsParam }),
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

      {/* ========== Agents Section ========== */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">
          <span className="text-orange-600">Agents</span> (Subagent Usage)
        </h2>
        {agentLoading ? (
          <p>Loading...</p>
        ) : !agentData || agentData.total_spawns === 0 ? (
          <p className="text-gray-500">No agent usage recorded. Re-import logs with <code className="bg-gray-100 px-1 rounded">claude-coach import --force</code> to populate.</p>
        ) : (
          <div className="space-y-6">
            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h3 className="text-xs font-medium text-orange-600">Total Spawns</h3>
                <p className="text-2xl font-bold text-orange-700">{agentData.total_spawns}</p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h3 className="text-xs font-medium text-orange-600">Agent Types</h3>
                <p className="text-2xl font-bold text-orange-700">{agentData.by_type.length}</p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h3 className="text-xs font-medium text-orange-600">Avg Tokens/Agent</h3>
                <p className="text-2xl font-bold text-orange-700">
                  {agentData.by_type.length > 0
                    ? formatTokens(Math.round(agentData.by_type.reduce((s, a) => s + a.avg_tokens, 0) / agentData.by_type.length))
                    : '0'}
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h3 className="text-xs font-medium text-orange-600">Avg Duration</h3>
                <p className="text-2xl font-bold text-orange-700">
                  {agentData.by_type.length > 0
                    ? formatDuration(Math.round(agentData.by_type.reduce((s, a) => s + a.avg_duration_ms, 0) / agentData.by_type.length))
                    : '-'}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Agent type distribution pie */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Distribution by Type</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={agentData.by_type.slice(0, 6)}
                      dataKey="count"
                      nameKey="subagent_type"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={(entry) => entry.subagent_type}
                    >
                      {agentData.by_type.slice(0, 6).map((_, index) => (
                        <Cell key={`agent-cell-${index}`} fill={AGENT_COLORS[index % AGENT_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Agent type bar chart */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Top Agent Types</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={agentData.by_type.slice(0, 8)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="subagent_type" type="category" width={120} fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#f97316" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Agent details table */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Detailed Stats by Type</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-2 text-left font-medium text-gray-600">Type</th>
                      <th className="px-4 py-2 text-right font-medium text-gray-600">Count</th>
                      <th className="px-4 py-2 text-right font-medium text-gray-600">Avg Tokens</th>
                      <th className="px-4 py-2 text-right font-medium text-gray-600">Avg Duration</th>
                      <th className="px-4 py-2 text-right font-medium text-gray-600">Total Tools</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentData.by_type.map((agent) => (
                      <tr key={agent.subagent_type} className="border-t">
                        <td className="px-4 py-2 font-medium">{agent.subagent_type}</td>
                        <td className="px-4 py-2 text-right">{agent.count}</td>
                        <td className="px-4 py-2 text-right">{formatTokens(Math.round(agent.avg_tokens))}</td>
                        <td className="px-4 py-2 text-right">{formatDuration(Math.round(agent.avg_duration_ms))}</td>
                        <td className="px-4 py-2 text-right">{agent.total_tool_use_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ========== Skills Section ========== */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">
          <span className="text-green-600">Skills</span>
        </h2>
        {skillLoading ? (
          <p>Loading...</p>
        ) : !skillData || skillData.total_invocations === 0 ? (
          <p className="text-gray-500">No skill usage recorded. Skills are invoked via the Skill tool in Claude Code.</p>
        ) : (
          <div className="space-y-4">
            <div className="bg-green-50 p-4 rounded-lg border border-green-200 inline-block">
              <h3 className="text-xs font-medium text-green-600">Total Invocations</h3>
              <p className="text-2xl font-bold text-green-700">{skillData.total_invocations}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {skillData.by_skill.map((skill) => (
                <div key={skill.skill_name} className="flex items-center justify-between bg-green-50 p-3 rounded-lg border border-green-200">
                  <span className="font-medium text-green-800">{skill.skill_name}</span>
                  <span className="text-sm font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded">{skill.count}x</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ========== MCP Section ========== */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">
          <span className="text-purple-600">MCP Servers</span>
        </h2>
        {mcpLoading ? (
          <p>Loading...</p>
        ) : !mcpData || mcpData.total_calls === 0 ? (
          <p className="text-gray-500">No MCP tool usage recorded. MCP tools appear as <code className="bg-gray-100 px-1 rounded">mcp__server__tool</code> in logs.</p>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <h3 className="text-xs font-medium text-purple-600">Total MCP Calls</h3>
                <p className="text-2xl font-bold text-purple-700">{mcpData.total_calls}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <h3 className="text-xs font-medium text-purple-600">MCP Servers</h3>
                <p className="text-2xl font-bold text-purple-700">{mcpData.by_server.length}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Server distribution bar chart */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Calls per Server</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={mcpData.by_server} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="server_name" type="category" width={120} fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="total_calls" fill="#a855f7" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Top tools per server */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Top Tools per Server</h3>
                <div className="space-y-3 max-h-[250px] overflow-y-auto">
                  {mcpData.by_server.map((server) => (
                    <div key={server.server_name} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-purple-700">{server.server_name}</span>
                        <span className="text-xs text-gray-500">{server.total_calls} calls</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {server.tools.slice(0, 5).map((tool) => (
                          <span key={tool.tool_name} className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                            {tool.tool_name.replace(`mcp__${server.server_name}__`, '')} ({tool.count})
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
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
