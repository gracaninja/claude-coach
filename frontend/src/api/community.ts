import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

export interface AnonymizedMetrics {
  period_start: string
  period_end: string
  total_sessions: number
  total_messages: number
  avg_messages_per_session: number
  avg_session_duration_minutes?: number
  total_input_tokens: number
  total_output_tokens: number
  total_cache_read_tokens: number
  avg_tokens_per_session: number
  tool_usage: Record<string, number>
  top_tools: string[]
  total_errors: number
  error_types: Record<string, number>
  cache_hit_rate: number
  avg_tools_per_session: number
}

export interface CommunityBenchmark {
  total_users: number
  data_period_days: number
  avg_sessions_per_day: number
  avg_messages_per_session: number
  avg_tokens_per_session: number
  avg_tools_per_session: number
  tokens_p50: number
  tokens_p90: number
  tools_p50: number
  tools_p90: number
  most_used_tools: string[]
  avg_error_rate: number
}

export interface UserComparison {
  user_sessions_per_day: number
  user_messages_per_session: number
  user_tokens_per_session: number
  user_tools_per_session: number
  user_error_rate: number
  user_cache_hit_rate: number
  benchmark: CommunityBenchmark
  sessions_percentile: number
  tokens_percentile: number
  efficiency_percentile: number
  insights: string[]
}

export interface Insight {
  category: string
  title: string
  description: string
  severity: string
  metric_value?: number
  metric_label?: string
}

export async function fetchAnonymizedMetrics(params: {
  start_date?: string
  end_date?: string
} = {}): Promise<AnonymizedMetrics> {
  const response = await api.get('/community/export', { params })
  return response.data
}

export async function fetchCommunityBenchmark(): Promise<CommunityBenchmark> {
  const response = await api.get('/community/benchmark')
  return response.data
}

export async function fetchUserComparison(days: number = 30): Promise<UserComparison> {
  const response = await api.get('/community/compare', { params: { days } })
  return response.data
}

export async function fetchInsights(): Promise<Insight[]> {
  const response = await api.get('/community/insights')
  return response.data
}

export function downloadMetricsJson(): void {
  const baseUrl = import.meta.env.VITE_API_URL || '/api'
  window.open(`${baseUrl}/community/export/json`, '_blank')
}
