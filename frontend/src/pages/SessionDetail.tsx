import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchSession, fetchSessionTimeline } from '../api/sessions'
import { fetchContextGrowth, fetchSessionErrors } from '../api/analytics'
import type { TimelineEvent } from '../api/sessions'

function getProjectName(projectPath?: string): string {
  if (!projectPath) return '-'
  const parts = projectPath.split('/')
  return parts[parts.length - 1] || projectPath
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function formatDuration(ms?: number): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

function formatTokens(n?: number): string {
  if (!n) return '0'
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return n.toString()
}

// Category badge styles
const categoryStyles: Record<string, { bg: string; text: string; label: string }> = {
  native: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Tool' },
  mcp: { bg: 'bg-purple-100', text: 'text-purple-700', label: 'MCP' },
  skill: { bg: 'bg-green-100', text: 'text-green-700', label: 'Skill' },
  agent: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Agent' },
}

function CategoryBadge({ category, label }: { category?: string; label: string }) {
  const style = categoryStyles[category || 'native'] || categoryStyles.native
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style.bg} ${style.text}`}>
      {label}
    </span>
  )
}

function TimelineEventCard({ event }: { event: TimelineEvent }) {
  const [expanded, setExpanded] = useState(false)

  if (event.type === 'user_message') {
    return (
      <div className="flex gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold">U</div>
        <div className="flex-1 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-blue-800">User</span>
            {event.timestamp && <span className="text-xs text-gray-400">{formatDate(event.timestamp)}</span>}
          </div>
          <p className="text-sm text-gray-700">{event.content_preview}</p>
        </div>
      </div>
    )
  }

  if (event.type === 'assistant_message') {
    return (
      <div className="flex gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-bold">A</div>
        <div className="flex-1 bg-gray-50 border-l-4 border-gray-300 rounded-r-lg p-3">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-800">Assistant</span>
              {event.model && <span className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">{event.model}</span>}
            </div>
            {event.input_tokens && (
              <span className="text-xs text-gray-500">
                {formatTokens(event.input_tokens)} in / {formatTokens(event.output_tokens)} out
              </span>
            )}
          </div>
          <p className="text-sm text-gray-700">{event.content_preview}</p>
        </div>
      </div>
    )
  }

  if (event.type === 'tool_call') {
    return (
      <div className="flex gap-3 ml-11">
        <div className="flex-1 bg-white border border-gray-200 rounded-lg p-2 flex items-center gap-2">
          <CategoryBadge category={event.category} label={event.category === 'mcp' ? `MCP:${event.mcp_server}` : event.tool_name || 'Tool'} />
          <span className="text-sm text-gray-600">{event.tool_name}</span>
        </div>
      </div>
    )
  }

  if (event.type === 'agent_spawn') {
    return (
      <div className="flex gap-3 ml-11">
        <div className="flex-1 bg-orange-50 border border-orange-200 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CategoryBadge category="agent" label={event.subagent_type || 'Agent'} />
              {event.agent_status && (
                <span className={`text-xs px-1.5 py-0.5 rounded ${event.agent_status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {event.agent_status}
                </span>
              )}
            </div>
            <button onClick={() => setExpanded(!expanded)} className="text-xs text-orange-600 hover:underline">
              {expanded ? 'Less' : 'More'}
            </button>
          </div>
          {event.agent_description && (
            <p className="text-sm text-gray-600 mt-1">{event.agent_description}</p>
          )}
          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            {event.agent_duration_ms != null && <span>Duration: {formatDuration(event.agent_duration_ms)}</span>}
            {event.agent_total_tokens != null && <span>Tokens: {formatTokens(event.agent_total_tokens)}</span>}
            {event.agent_total_tool_count != null && <span>Tools: {event.agent_total_tool_count}</span>}
          </div>
        </div>
      </div>
    )
  }

  if (event.type === 'skill_invoke') {
    return (
      <div className="flex gap-3 ml-11">
        <div className="flex-1 bg-green-50 border border-green-200 rounded-lg p-2 flex items-center gap-2">
          <CategoryBadge category="skill" label="Skill" />
          <span className="text-sm text-green-700 font-medium">{event.skill_name}</span>
        </div>
      </div>
    )
  }

  if (event.type === 'error') {
    return (
      <div className="flex gap-3 ml-11">
        <div className="flex-1 bg-red-50 border border-red-200 rounded-lg p-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded font-medium">{event.error_type}</span>
          </div>
          {event.error_message && <p className="text-sm text-red-700 mt-1 line-clamp-2">{event.error_message}</p>}
        </div>
      </div>
    )
  }

  return null
}

function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [viewMode, setViewMode] = useState<'timeline' | 'conversation'>('timeline')

  const { data: session, isLoading, error } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => fetchSession(sessionId!),
    enabled: !!sessionId,
  })

  const { data: timeline } = useQuery({
    queryKey: ['sessionTimeline', sessionId],
    queryFn: () => fetchSessionTimeline(sessionId!),
    enabled: !!sessionId,
  })

  const { data: contextData } = useQuery({
    queryKey: ['contextGrowth', sessionId],
    queryFn: () => fetchContextGrowth(sessionId!),
    enabled: !!sessionId,
  })

  const { data: errorData } = useQuery({
    queryKey: ['sessionErrors', sessionId],
    queryFn: () => fetchSessionErrors(sessionId!),
    enabled: !!sessionId,
  })

  if (isLoading) return <div>Loading session...</div>
  if (error) return <div>Error loading session</div>
  if (!session) return <div>Session not found</div>

  const summary = timeline?.summary

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/sessions" className="text-indigo-600 hover:text-indigo-800">
          &larr; Back to Sessions
        </Link>
        <h1 className="text-2xl font-bold">Session Detail</h1>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Session Info</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-500">Project:</span>{' '}
            <span className="text-gray-900">{getProjectName(session.project_path)}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Branch:</span>{' '}
            <span className="text-gray-900">{session.git_branch || '-'}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Created:</span>{' '}
            <span className="text-gray-900">{formatDate(session.created)}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Modified:</span>{' '}
            <span className="text-gray-900">{formatDate(session.modified)}</span>
          </div>
          <div className="md:col-span-2">
            <span className="font-medium text-gray-500">Full Path:</span>{' '}
            <span className="text-gray-700 font-mono text-xs">{session.project_path || '-'}</span>
          </div>
        </div>
        {session.first_prompt && (
          <div className="mt-4 pt-4 border-t">
            <span className="font-medium text-gray-500">First Prompt:</span>
            <p className="text-gray-900 mt-1">{session.first_prompt}</p>
          </div>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-xs font-medium text-gray-500">Input Tokens</h3>
          <p className="text-xl font-bold">{formatTokens(session.total_input_tokens)}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-xs font-medium text-gray-500">Output Tokens</h3>
          <p className="text-xl font-bold">{formatTokens(session.total_output_tokens)}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-xs font-medium text-gray-500">Tool Calls</h3>
          <p className="text-xl font-bold">{session.tool_call_count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-xs font-medium text-gray-500">Errors</h3>
          <p className="text-xl font-bold">{session.error_count}</p>
        </div>
        {summary && summary.agent_spawns > 0 && (
          <div className="bg-orange-50 p-4 rounded-lg shadow border border-orange-200">
            <h3 className="text-xs font-medium text-orange-600">Agents</h3>
            <p className="text-xl font-bold text-orange-700">{summary.agent_spawns}</p>
          </div>
        )}
        {summary && summary.skill_invocations > 0 && (
          <div className="bg-green-50 p-4 rounded-lg shadow border border-green-200">
            <h3 className="text-xs font-medium text-green-600">Skills</h3>
            <p className="text-xl font-bold text-green-700">{summary.skill_invocations}</p>
          </div>
        )}
        {summary && summary.mcp_tool_calls > 0 && (
          <div className="bg-purple-50 p-4 rounded-lg shadow border border-purple-200">
            <h3 className="text-xs font-medium text-purple-600">MCP Calls</h3>
            <p className="text-xl font-bold text-purple-700">{summary.mcp_tool_calls}</p>
          </div>
        )}
      </div>

      {contextData && contextData.data.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Context Size Growth</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={contextData.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="message_index" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="context_tokens" stroke="#6366f1" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Error Analysis Section */}
      {errorData && errorData.total_errors > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">
            Tool Errors ({errorData.total_errors})
          </h2>

          {/* Error Categories with Suggestions */}
          <div className="space-y-3 mb-6">
            {errorData.by_category.map((cat) => (
              <div key={cat.category} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium capitalize">
                    {cat.category.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm font-semibold text-red-600">{cat.count}</span>
                </div>
                <p className="text-sm text-gray-600">{cat.description}</p>
                <div className="mt-2 bg-blue-50 p-2 rounded text-sm">
                  <span className="font-medium text-blue-700">Suggestion: </span>
                  <span className="text-blue-600">{cat.suggestion}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Individual Errors */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700">Error Details</h3>
            {errorData.errors.slice(0, 10).map((err, idx) => (
              <div key={idx} className="bg-red-50 p-3 rounded text-sm">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded">
                    {err.tool_name}
                  </span>
                  <span className="text-xs text-gray-500 capitalize">
                    {err.error_category.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="text-gray-700 line-clamp-2">{err.error_message}</p>
              </div>
            ))}
            {errorData.errors.length > 10 && (
              <p className="text-sm text-gray-500">
                ... and {errorData.errors.length - 10} more errors
              </p>
            )}
          </div>
        </div>
      )}

      {/* View mode toggle */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {viewMode === 'timeline' ? 'Session Timeline' : 'Conversation'}
          </h2>
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition ${
                viewMode === 'timeline'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setViewMode('conversation')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition ${
                viewMode === 'conversation'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Conversation
            </button>
          </div>
        </div>

        {viewMode === 'timeline' && timeline ? (
          <div className="space-y-3">
            {timeline.events.length === 0 ? (
              <p className="text-gray-500 text-sm">No timeline data available. Try re-importing with <code className="bg-gray-100 px-1 rounded">claude-coach import --force</code></p>
            ) : (
              timeline.events.map((event, idx) => (
                <TimelineEventCard key={idx} event={event} />
              ))
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {session.messages.map((message, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-50 border-l-4 border-blue-500'
                    : 'bg-gray-50 border-l-4 border-gray-300'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium capitalize">{message.role}</span>
                  {message.input_tokens && (
                    <span className="text-xs text-gray-500">
                      {message.input_tokens} in / {message.output_tokens} out
                    </span>
                  )}
                </div>
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default SessionDetail
