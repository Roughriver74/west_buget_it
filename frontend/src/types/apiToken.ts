/**
 * API Token types for External API authentication
 */

export type APITokenStatus = 'ACTIVE' | 'REVOKED' | 'EXPIRED';

export type APITokenScope = 'READ' | 'WRITE' | 'DELETE' | 'ADMIN';

export interface APIToken {
  id: number;
  name: string;
  description?: string;
  scopes: APITokenScope[];
  status: APITokenStatus;
  department_id?: number;
  created_at: string;
  created_by: number;
  expires_at?: string;
  last_used_at?: string;
  revoked_at?: string;
  revoked_by?: number;
  request_count: number;
}

export interface APITokenWithKey extends APIToken {
  token_key: string; // Only returned once during creation!
}

export interface CreateTokenRequest {
  name: string;
  description?: string;
  scopes: APITokenScope[];
  department_id?: number;
  expires_at?: string;
}

export interface UpdateTokenRequest {
  name?: string;
  description?: string;
  scopes?: APITokenScope[];
  status?: APITokenStatus;
  expires_at?: string;
}

export interface RevokeTokenRequest {
  reason?: string;
}

export interface TokensListParams {
  skip?: number;
  limit?: number;
  status_filter?: APITokenStatus;
  department_id?: number;
}
