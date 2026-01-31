import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchSessions, fetchFilters } from '../api/sessions'
import { useProjectFilter } from '../context/ProjectContext'

function getProjectName(projectPath: string): string {
  if (!projectPath) return '-'
  const parts = projectPath.split('/')
  return parts[parts.length - 1] || projectPath
}

function Sessions() {
  const [selectedBranch, setSelectedBranch] = useState<string>('')
  const { projectsParam } = useProjectFilter()

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: fetchFilters,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['sessions', projectsParam, selectedBranch],
    queryFn: () => fetchSessions({
      limit: 50,
      project: projectsParam,
      branch: selectedBranch || undefined,
    }),
  })

  if (isLoading) return <div>Loading sessions...</div>
  if (error) return <div>Error loading sessions</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Sessions</h1>

      <div className="mb-4 flex gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
          <select
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            className="block w-48 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Branches</option>
            {filters?.branches.map((branch) => (
              <option key={branch} value={branch}>
                {branch}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="text-sm text-gray-500 mb-2">
        Showing {data?.sessions?.length || 0} of {data?.total || 0} sessions
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                First Prompt
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Project
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
                    {session.first_prompt?.slice(0, 60) || 'No prompt'}
                    {(session.first_prompt?.length || 0) > 60 ? '...' : ''}
                  </Link>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {getProjectName(session.project_path)}
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
