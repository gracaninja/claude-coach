import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchSessions } from '../api/sessions'

function Sessions() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => fetchSessions({ limit: 50 }),
  })

  if (isLoading) return <div>Loading sessions...</div>
  if (error) return <div>Error loading sessions</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Sessions</h1>
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                First Prompt
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Messages
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Branch
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data?.sessions?.map((session) => (
              <tr key={session.session_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <Link
                    to={`/sessions/${session.session_id}`}
                    className="text-indigo-600 hover:text-indigo-900"
                  >
                    {session.first_prompt || 'No prompt'}
                  </Link>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {session.message_count}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {session.created?.slice(0, 10)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {session.git_branch || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Sessions
