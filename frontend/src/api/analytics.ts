import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

export interface TokenDataPoint {
  date: string
  input_tokens: number
  output_tokens: number
  cache_read_tokens: number
  cache_creation_tokens: number
}

export interface TokenUsageResponse {
  data: TokenDataPoint[]
  total_input_tokens: number
  total_output_tokens: number
}

export interface ToolDataPoint {
  tool_name: string
  count: number
}

export interface ToolUsageResponse {
  data: ToolDataPoint[]
  total_tool_calls: number
}

export interface ErrorDataPoint {
  error_type: string
  count: number
}

export interface ErrorStatsResponse {
  data: ErrorDataPoint[]
  total_errors: number
}

export interface ContextDataPoint {
  message_index: number
  context_tokens: number
  timestamp?: string
}

export interface ContextGrowthResponse {
  session_id: string
  data: ContextDataPoint[]
}

export async function fetchTokenUsage(params: {
  start_date?: string
  end_date?: string
  session_id?: string
  project?: string[]
} = {}): Promise<TokenUsageResponse> {
  const response = await api.get('/analytics/tokens', { params, paramsSerializer: { indexes: null } })
  return response.data
}

export async function fetchToolUsage(params: {
  start_date?: string
  end_date?: string
  project?: string[]
} = {}): Promise<ToolUsageResponse> {
  const response = await api.get('/analytics/tools', { params, paramsSerializer: { indexes: null } })
  return response.data
}

export async function fetchErrorStats(params: {
  start_date?: string
  end_date?: string
  project?: string[]
} = {}): Promise<ErrorStatsResponse> {
  const response = await api.get('/analytics/errors', { params, paramsSerializer: { indexes: null } })
  return response.data
}

export async function fetchContextGrowth(sessionId: string): Promise<ContextGrowthResponse> {
  const response = await api.get(`/analytics/context-growth/${sessionId}`)
  return response.data
}

export interface PlanModeSessionStats {
  session_id: string
  planning_time_seconds: number
  execution_time_seconds: number
  planning_tokens: number
  execution_tokens: number
  planning_messages: number
  execution_messages: number
  plan_mode_entries: number
  planning_percentage: number
}

export interface PlanModeAggregateStats {
  total_planning_time_seconds: number
  total_execution_time_seconds: number
  total_planning_tokens: number
  total_execution_tokens: number
  total_planning_messages: number
  total_execution_messages: number
  total_plan_mode_entries: number
  avg_planning_percentage: number
  sessions_with_planning: number
  total_sessions: number
}

export interface PlanModeResponse {
  aggregate: PlanModeAggregateStats
  sessions: PlanModeSessionStats[]
}

export async function fetchPlanModeStats(): Promise<PlanModeResponse> {
  const response = await api.get('/analytics/plan-mode')
  return response.data
}

// Error Analysis types
export interface ToolErrorDetail {
  tool_name: string
  error_message: string
  error_category: string
  timestamp?: string
  session_id: string
  project_path?: string
  tool_input?: Record<string, unknown>
}

export interface SubcategoryDetail {
  count: number
  example?: string
}

export interface ErrorCategorySummary {
  category: string
  count: number
  description: string
  suggestion: string
  example_errors: string[]
  subcategories?: Record<string, SubcategoryDetail>
}

export interface ToolErrorSummary {
  tool_name: string
  total_errors: number
  by_category: Record<string, number>
}

export interface ActionableIssue {
  issue_type: string
  description: string
  fix: string
  count: number
  projects: string[]
  examples: string[]
}

export interface ErrorAnalysisResponse {
  total_errors: number
  by_category: ErrorCategorySummary[]
  by_tool: ToolErrorSummary[]
  recent_errors: ToolErrorDetail[]
  actionable_issues: ActionableIssue[]
}

export interface DailyErrorSummary {
  date: string
  total: number
  by_category: Record<string, number>
}

export interface TimeframeErrorsResponse {
  days: number
  total_errors: number
  daily: DailyErrorSummary[]
  actionable_issues: ActionableIssue[]
}

export interface SessionErrorsResponse {
  session_id: string
  project_path?: string
  total_errors: number
  by_category: ErrorCategorySummary[]
  errors: ToolErrorDetail[]
}

export async function fetchErrorAnalysis(params: {
  project?: string
  limit?: number
} = {}): Promise<ErrorAnalysisResponse> {
  const response = await api.get('/analytics/error-analysis', { params })
  return response.data
}

export async function fetchErrorsByTimeframe(params: {
  days?: number
  project?: string
} = {}): Promise<TimeframeErrorsResponse> {
  const response = await api.get('/analytics/error-analysis/timeframe', { params })
  return response.data
}

export async function fetchSessionErrors(sessionId: string): Promise<SessionErrorsResponse> {
  const response = await api.get(`/analytics/error-analysis/session/${sessionId}`)
  return response.data
}

// ========== Agent Analytics ==========

export interface AgentTypeStats {
  subagent_type: string
  count: number
  total_tokens: number
  total_duration_ms: number
  avg_tokens: number
  avg_duration_ms: number
  total_tool_use_count: number
}

export interface AgentDailyCount {
  date: string
  count: number
}

export interface AgentAnalyticsResponse {
  total_spawns: number
  by_type: AgentTypeStats[]
  daily_trend: AgentDailyCount[]
}

export async function fetchAgentAnalytics(params: {
  project?: string[]
  start_date?: string
  end_date?: string
} = {}): Promise<AgentAnalyticsResponse> {
  const response = await api.get('/analytics/agents', { params, paramsSerializer: { indexes: null } })
  return response.data
}

// ========== Skill Analytics ==========

export interface SkillStats {
  skill_name: string
  count: number
}

export interface SkillDailyCount {
  date: string
  count: number
}

export interface SkillAnalyticsResponse {
  total_invocations: number
  by_skill: SkillStats[]
  daily_trend: SkillDailyCount[]
}

export async function fetchSkillAnalytics(params: {
  project?: string[]
  start_date?: string
  end_date?: string
} = {}): Promise<SkillAnalyticsResponse> {
  const response = await api.get('/analytics/skills', { params, paramsSerializer: { indexes: null } })
  return response.data
}

// ========== MCP Analytics ==========

export interface McpToolStats {
  tool_name: string
  count: number
}

export interface McpServerStats {
  server_name: string
  total_calls: number
  tools: McpToolStats[]
}

export interface McpAnalyticsResponse {
  total_calls: number
  by_server: McpServerStats[]
}

export async function fetchMcpAnalytics(params: {
  project?: string[]
  start_date?: string
  end_date?: string
} = {}): Promise<McpAnalyticsResponse> {
  const response = await api.get('/analytics/mcp', { params, paramsSerializer: { indexes: null } })
  return response.data
}
