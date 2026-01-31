import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchTokenUsage, fetchToolUsage } from '../api/analytics'
import { fetchSessions } from '../api/sessions'
import { useProjectFilter } from '../context/ProjectContext'

function Dashboard() {
  const { projectsParam } = useProjectFilter()

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions', projectsParam],
    queryFn: () => fetchSessions({ limit: 5, project: projectsParam }),
  })

  const { data: tokenData, isLoading: tokenLoading } = useQuery({
    queryKey: ['tokenUsage', projectsParam],
    queryFn: () => fetchTokenUsage({ project: projectsParam }),
  })

  const { data: toolData, isLoading: toolLoading } = useQuery({
    queryKey: ['toolUsage', projectsParam],
    queryFn: () => fetchToolUsage({ project: projectsParam }),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Sessions</h3>
          <p className="text-3xl font-bold">{sessions?.total ?? '-'}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Tokens Used</h3>
          <p className="text-3xl font-bold">
            {tokenData ? (tokenData.total_input_tokens + tokenData.total_output_tokens).toLocaleString() : '-'}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Tool Calls</h3>
          <p className="text-3xl font-bold">{toolData?.total_tool_calls?.toLocaleString() ?? '-'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Token Usage Over Time</h2>
          {tokenLoading ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={tokenData?.data ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="input_tokens" fill="#6366f1" name="Input" />
                <Bar dataKey="output_tokens" fill="#22c55e" name="Output" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Tool Usage</h2>
          {toolLoading ? (
            <p>Loading...</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={toolData?.data?.slice(0, 10) ?? []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="tool_name" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Recent Sessions</h2>
          <Link to="/sessions" className="text-indigo-600 hover:text-indigo-800">
            View all
          </Link>
        </div>
        {sessionsLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="space-y-2">
            {sessions?.sessions?.map((session) => (
              <Link
                key={session.session_id}
                to={`/sessions/${session.session_id}`}
                className="block p-3 hover:bg-gray-50 rounded border"
              >
                <div className="flex justify-between">
                  <span className="font-medium truncate">{session.first_prompt || 'No prompt'}</span>
                  <span className="text-gray-500 text-sm">{session.message_count} messages</span>
                </div>
                <div className="text-gray-500 text-sm">{session.created?.slice(0, 10)}</div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
