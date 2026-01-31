import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchSession } from '../api/sessions'
import { fetchContextGrowth, fetchSessionErrors } from '../api/analytics'

function getProjectName(projectPath?: string): string {
  if (!projectPath) return '-'
  const parts = projectPath.split('/')
  return parts[parts.length - 1] || projectPath
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()

  const { data: session, isLoading, error } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => fetchSession(sessionId!),
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Input Tokens</h3>
          <p className="text-2xl font-bold">{session.total_input_tokens.toLocaleString()}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Output Tokens</h3>
          <p className="text-2xl font-bold">{session.total_output_tokens.toLocaleString()}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Tool Calls</h3>
          <p className="text-2xl font-bold">{session.tool_call_count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Errors</h3>
          <p className="text-2xl font-bold">{session.error_count}</p>
        </div>
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

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Conversation</h2>
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
      </div>
    </div>
  )
}

export default SessionDetail
