import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
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
} from 'recharts'
import {
  fetchErrorAnalysis,
  fetchErrorsByTimeframe,
  ErrorCategorySummary,
  ToolErrorDetail,
  ActionableIssue,
} from '../api/analytics'
import { useProjectFilter } from '../context/ProjectContext'

const CATEGORY_COLORS: Record<string, string> = {
  file_not_found: '#ef4444',
  directory_instead_of_file: '#f97316',
  tool_not_available: '#8b5cf6',
  user_rejected: '#6b7280',
  edit_string_not_found: '#eab308',
  edit_multiple_matches: '#f59e0b',
  file_not_read_first: '#ec4899',
  command_failed: '#dc2626',
  http_error: '#3b82f6',
  file_too_large: '#14b8a6',
  database_connection: '#a855f7',
  mcp_workspace_not_set: '#06b6d4',
  task_interrupted: '#9ca3af',
  permission_denied: '#b91c1c',
  invalid_input: '#f43f5e',
  other: '#64748b',
}

function ErrorAnalysis() {
  const { selectedProjects, isAllSelected } = useProjectFilter()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [timeframeDays, setTimeframeDays] = useState(7)

  // Determine project filter for API call
  const projectFilter = isAllSelected
    ? undefined
    : selectedProjects.length === 1
    ? selectedProjects[0]
    : undefined

  const { data, isLoading, error } = useQuery({
    queryKey: ['errorAnalysis', projectFilter],
    queryFn: () => fetchErrorAnalysis({ project: projectFilter, limit: 1000 }),
  })

  const { data: timeframeData } = useQuery({
    queryKey: ['errorTimeframe', projectFilter, timeframeDays],
    queryFn: () => fetchErrorsByTimeframe({ project: projectFilter, days: timeframeDays }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading error analysis...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-lg">
        <p className="text-red-600">Failed to load error analysis</p>
      </div>
    )
  }

  const filteredErrors = selectedCategory
    ? data?.recent_errors.filter((e) => e.error_category === selectedCategory)
    : data?.recent_errors

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Error Analysis</h1>
        <span className="text-gray-500">
          {data?.total_errors.toLocaleString()} total errors analyzed
        </span>
      </div>

      {/* Actionable Issues - Most Important! */}
      {data?.actionable_issues && data.actionable_issues.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 p-6 rounded-lg">
          <h2 className="text-lg font-semibold text-amber-900 mb-4">
            Actionable Issues - Things You Can Fix
          </h2>
          <div className="space-y-4">
            {data.actionable_issues.map((issue) => (
              <ActionableIssueCard key={issue.issue_type} issue={issue} />
            ))}
          </div>
        </div>
      )}

      {/* Error Trend Over Time */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Error Trend</h2>
          <div className="flex gap-2">
            {[7, 14, 30].map((days) => (
              <button
                key={days}
                onClick={() => setTimeframeDays(days)}
                className={`px-3 py-1 text-sm rounded ${
                  timeframeDays === days
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>
        {timeframeData && timeframeData.daily.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timeframeData.daily}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                fontSize={12}
                tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(d) => new Date(d).toLocaleDateString()}
                formatter={(value: number) => [value, 'Errors']}
              />
              <Line type="monotone" dataKey="total" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-8">No error data for this timeframe</p>
        )}
      </div>

      {/* Error Categories with Drill-Down */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Error Categories</h2>
        <div className="space-y-4">
          {data?.by_category.map((cat) => (
            <ErrorCategoryCard
              key={cat.category}
              category={cat}
              isSelected={selectedCategory === cat.category}
              onClick={() =>
                setSelectedCategory(
                  selectedCategory === cat.category ? null : cat.category
                )
              }
            />
          ))}
        </div>
      </div>

      {/* Errors by Tool */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Errors by Tool</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data?.by_tool.slice(0, 10) ?? []} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="tool_name" type="category" width={120} fontSize={12} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const tool = payload[0].payload
                  return (
                    <div className="bg-white p-3 shadow-lg rounded border">
                      <p className="font-semibold">{tool.tool_name}</p>
                      <p className="text-sm text-gray-600">
                        Total: {tool.total_errors} errors
                      </p>
                      <div className="text-xs mt-1">
                        {Object.entries(tool.by_category)
                          .sort((a, b) => (b[1] as number) - (a[1] as number))
                          .slice(0, 5)
                          .map(([cat, count]) => (
                            <div key={cat}>
                              {cat}: {count as number}
                            </div>
                          ))}
                      </div>
                    </div>
                  )
                }
                return null
              }}
            />
            <Bar dataKey="total_errors" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Errors List */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {selectedCategory
              ? `${selectedCategory.replace(/_/g, ' ')} errors`
              : 'Recent Errors'}
          </h2>
          {selectedCategory && (
            <button
              onClick={() => setSelectedCategory(null)}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Clear filter
            </button>
          )}
        </div>
        <div className="space-y-3 max-h-[500px] overflow-y-auto">
          {filteredErrors?.map((error, index) => (
            <ErrorDetailCard key={index} error={error} />
          ))}
          {filteredErrors?.length === 0 && (
            <p className="text-gray-500">No errors found</p>
          )}
        </div>
      </div>
    </div>
  )
}

function ActionableIssueCard({ issue }: { issue: ActionableIssue }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white border border-amber-300 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-amber-600">{issue.count}</span>
            <div>
              <h3 className="font-medium text-gray-900">
                {issue.issue_type.replace(/_/g, ' ')}
              </h3>
              <p className="text-sm text-gray-600">{issue.description}</p>
            </div>
          </div>
          <div className="mt-3 bg-green-50 p-3 rounded text-sm border border-green-200">
            <span className="font-semibold text-green-800">How to fix: </span>
            <span className="text-green-700">{issue.fix}</span>
          </div>
          {expanded && (
            <div className="mt-3 text-xs text-gray-500">
              <p className="font-medium">Affected projects:</p>
              <ul className="list-disc list-inside">
                {issue.projects.slice(0, 3).map((p, i) => (
                  <li key={i} className="truncate">{p}</li>
                ))}
              </ul>
              {issue.examples.length > 0 && (
                <>
                  <p className="font-medium mt-2">Example errors:</p>
                  {issue.examples.slice(0, 2).map((ex, i) => (
                    <p key={i} className="text-gray-400 truncate">{ex}</p>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-600 ml-2"
        >
          {expanded ? '−' : '+'}
        </button>
      </div>
    </div>
  )
}

function ErrorCategoryCard({
  category,
  isSelected,
  onClick,
}: {
  category: ErrorCategorySummary
  isSelected: boolean
  onClick: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const color = CATEGORY_COLORS[category.category] || CATEGORY_COLORS.other
  const hasSubcategories = category.subcategories && Object.keys(category.subcategories).length > 0

  return (
    <div
      className={`border rounded-lg p-4 transition-all ${
        isSelected ? 'ring-2 ring-indigo-500 border-indigo-300' : 'hover:border-gray-400'
      }`}
    >
      <div
        className="flex items-start justify-between cursor-pointer"
        onClick={onClick}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <div>
            <h3 className="font-medium capitalize">
              {category.category.replace(/_/g, ' ')}
            </h3>
            <p className="text-sm text-gray-600">{category.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold" style={{ color }}>
            {category.count}
          </span>
          {hasSubcategories && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setExpanded(!expanded)
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              {expanded ? '▼' : '▶'}
            </button>
          )}
        </div>
      </div>

      {/* Subcategories drill-down */}
      {expanded && hasSubcategories && (
        <div className="mt-3 ml-6 space-y-1">
          <p className="text-xs font-medium text-gray-500 uppercase">Breakdown:</p>
          {Object.entries(category.subcategories!)
            .sort((a, b) => b[1].count - a[1].count)
            .map(([subcat, details]) => (
              <div key={subcat} className="flex items-center justify-between text-sm">
                <span className="text-gray-700">{subcat.replace(/_/g, ' ')}</span>
                <span className="text-gray-500">{details.count}</span>
              </div>
            ))}
        </div>
      )}

      <div className="mt-3 bg-blue-50 p-3 rounded text-sm">
        <span className="font-medium text-blue-700">Suggestion: </span>
        <span className="text-blue-600">{category.suggestion}</span>
      </div>
    </div>
  )
}

function ErrorDetailCard({ error }: { error: ToolErrorDetail }) {
  const [expanded, setExpanded] = useState(false)
  const color = CATEGORY_COLORS[error.error_category] || CATEGORY_COLORS.other

  return (
    <div className="border rounded-lg p-3 text-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="px-2 py-0.5 rounded text-xs font-medium text-white"
              style={{ backgroundColor: color }}
            >
              {error.tool_name}
            </span>
            <span className="text-xs text-gray-500 capitalize">
              {error.error_category.replace(/_/g, ' ')}
            </span>
          </div>
          <p className={`text-gray-700 ${expanded ? '' : 'line-clamp-2'}`}>
            {error.error_message}
          </p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-600 ml-2"
        >
          {expanded ? '−' : '+'}
        </button>
      </div>
      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
        <Link
          to={`/sessions/${error.session_id}`}
          className="text-indigo-600 hover:underline"
        >
          View Session
        </Link>
        {error.timestamp && (
          <span>{new Date(error.timestamp).toLocaleString()}</span>
        )}
        {error.project_path && (
          <span className="truncate max-w-[200px]">{error.project_path}</span>
        )}
      </div>
      {expanded && error.tool_input && (
        <div className="mt-2 bg-gray-50 p-2 rounded text-xs font-mono overflow-x-auto">
          <pre>{JSON.stringify(error.tool_input, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default ErrorAnalysis
