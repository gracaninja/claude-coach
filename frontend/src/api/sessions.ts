import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

export interface Session {
  session_id: string
  project_path: string
  first_prompt: string
  summary?: string
  message_count: number
  created?: string
  modified?: string
  git_branch?: string
}

export interface Message {
  role: string
  content: string
  timestamp?: string
  model?: string
  input_tokens?: number
  output_tokens?: number
}

export interface SessionDetail {
  session_id: string
  project_path?: string
  git_branch?: string
  first_prompt?: string
  created?: string
  modified?: string
  messages: Message[]
  total_input_tokens: number
  total_output_tokens: number
  total_cache_read_tokens: number
  total_cache_creation_tokens: number
  tool_call_count: number
  error_count: number
}

export interface FiltersResponse {
  projects: string[]
  branches: string[]
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

export async function fetchSessions(params: { limit?: number; offset?: number; project?: string[]; branch?: string } = {}): Promise<SessionListResponse> {
  const response = await api.get('/sessions', { params, paramsSerializer: { indexes: null } })
  return response.data
}

export async function fetchFilters(): Promise<FiltersResponse> {
  const response = await api.get('/sessions/filters')
  return response.data
}

export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  const response = await api.get(`/sessions/${sessionId}`)
  return response.data
}

// Timeline types and fetch

export interface TimelineEvent {
  type: string // user_message, assistant_message, tool_call, agent_spawn, skill_invoke, error
  timestamp?: string
  role?: string
  content_preview?: string
  model?: string
  input_tokens?: number
  output_tokens?: number
  tool_name?: string
  category?: string // native, mcp, skill, agent
  mcp_server?: string
  subagent_type?: string
  agent_description?: string
  agent_duration_ms?: number
  agent_total_tokens?: number
  agent_total_tool_count?: number
  agent_status?: string
  skill_name?: string
  error_type?: string
  error_message?: string
}

export interface TimelineSummary {
  total_messages: number
  total_tool_calls: number
  native_tool_calls: number
  mcp_tool_calls: number
  agent_spawns: number
  skill_invocations: number
  errors: number
  total_tokens: number
  duration_ms?: number
}

export interface SessionTimelineResponse {
  session_id: string
  events: TimelineEvent[]
  summary: TimelineSummary
}

export async function fetchSessionTimeline(sessionId: string): Promise<SessionTimelineResponse> {
  const response = await api.get(`/sessions/${sessionId}/timeline`)
  return response.data
}
