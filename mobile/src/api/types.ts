export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  device_id: string;
}

export interface VoiceProcessResponse {
  transcript: string;
  emotion_state: string;
  response_text: string;
  proposed_action_id: string | null;
  audio_response_url: string | null;
}

export interface ProposedAction {
  id: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  summary: string;
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'failed' | 'expired';
  created_at: string;
}

export interface ActionExecutionResult {
  id: string;
  status: string;
  result: string | null;
  error: string | null;
  executed_at: string | null;
}

export interface ConversationTurn {
  id: string;
  transcript: string;
  response: string;
  emotion_state: string;
  created_at: string;
}

export interface UserContextResponse {
  user_id: string;
  display_name: string;
  recent_interactions: ConversationTurn[];
  document_count: number;
}
