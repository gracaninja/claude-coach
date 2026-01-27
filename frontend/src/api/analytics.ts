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
} = {}): Promise<TokenUsageResponse> {
  const response = await api.get('/analytics/tokens', { params })
  return response.data
}

export async function fetchToolUsage(params: {
  start_date?: string
  end_date?: string
} = {}): Promise<ToolUsageResponse> {
  const response = await api.get('/analytics/tools', { params })
  return response.data
}

export async function fetchErrorStats(params: {
  start_date?: string
  end_date?: string
} = {}): Promise<ErrorStatsResponse> {
  const response = await api.get('/analytics/errors', { params })
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
