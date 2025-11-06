import apiClient from './client';
import type {
  APIToken,
  APITokenWithKey,
  CreateTokenRequest,
  UpdateTokenRequest,
  RevokeTokenRequest,
  TokensListParams
} from '../types/apiToken';

/**
 * Get list of API tokens
 */
export const getTokens = async (params?: TokensListParams): Promise<APIToken[]> => {
  const { data } = await apiClient.get('/api-tokens/', { params });
  return data;
};

/**
 * Create a new API token
 * @returns Token with token_key - SHOWN ONLY ONCE!
 */
export const createToken = async (request: CreateTokenRequest): Promise<APITokenWithKey> => {
  const { data } = await apiClient.post('/api-tokens/', request);
  return data;
};

/**
 * Update an existing API token
 */
export const updateToken = async (
  tokenId: number,
  request: UpdateTokenRequest
): Promise<APIToken> => {
  const { data } = await apiClient.put(`/api-tokens/${tokenId}/`, request);
  return data;
};

/**
 * Revoke an API token (irreversible)
 */
export const revokeToken = async (
  tokenId: number,
  request?: RevokeTokenRequest
): Promise<APIToken> => {
  const { data } = await apiClient.post(`/api-tokens/${tokenId}/revoke/`, request);
  return data;
};

/**
 * Delete an API token permanently (dangerous!)
 */
export const deleteToken = async (tokenId: number): Promise<void> => {
  await apiClient.delete(`/api-tokens/${tokenId}/`);
};
