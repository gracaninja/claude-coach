import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchSession } from '../api/sessions'
import { fetchContextGrowth } from '../api/analytics'

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
