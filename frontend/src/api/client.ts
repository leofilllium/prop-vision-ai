/**
 * Axios API client with API key and JWT auth interceptors.
 */

import axios from 'axios';
import { config } from '../config';
import type { PropertyListResponse, SearchResponse, ComfortScoreDetail, DashboardData, Property } from '../types';

const AUTH_TOKEN_KEY = 'pv_access_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': config.apiKey,
  },
  timeout: 160000,
});

// Attach JWT token if present
apiClient.interceptors.request.use((req) => {
  const token = getStoredToken();
  if (token) {
    req.headers['Authorization'] = `Bearer ${token}`;
  }
  return req;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      console.warn('Rate limited. Retry after:', error.response.headers['retry-after']);
    }
    return Promise.reject(error);
  }
);

// ── Property API ──────────────────────────────

export async function fetchProperties(params?: {
  district?: string;
  min_price?: number;
  max_price?: number;
  rooms?: number;
  bbox?: string;
  limit?: number;
  offset?: number;
}): Promise<PropertyListResponse> {
  const { data } = await apiClient.get('/properties', { params });
  return data;
}

export async function fetchProperty(id: string): Promise<Property> {
  const { data } = await apiClient.get(`/properties/${id}`);
  return data;
}

// ── Search API ────────────────────────────────

export async function searchProperties(query: string): Promise<SearchResponse> {
  const { data } = await apiClient.post('/search', { query });
  return data;
}

// ── Comfort API ───────────────────────────────

export async function fetchComfortScores(propertyId: string): Promise<ComfortScoreDetail> {
  const { data } = await apiClient.get(`/comfort/${propertyId}`);
  return data;
}

// ── Analytics API ─────────────────────────────

export async function fetchDashboard(): Promise<DashboardData> {
  const { data } = await apiClient.get('/analytics/dashboard');
  return data;
}

// ── Video Walkthrough API ──────────────────────────

export async function generateVideoWalkthrough(propertyId: string) {
  const { data } = await apiClient.post(`/video/generate/${propertyId}`);
  return data;
}

export async function fetchVideoStatus(propertyId: string) {
  const { data } = await apiClient.get(`/video/${propertyId}/status`);
  return data;
}

// ── Auth API ──────────────────────────────────

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface UserInfo {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

export async function apiLogin(email: string, password: string): Promise<AuthToken> {
  const { data } = await apiClient.post('/auth/login', { email, password });
  return data;
}

export async function apiRegister(email: string, password: string): Promise<UserInfo> {
  const { data } = await apiClient.post('/auth/register', { email, password });
  return data;
}

export async function apiGetMe(): Promise<UserInfo> {
  const { data } = await apiClient.get('/auth/me');
  return data;
}

// ── Admin API ──────────────────────────────

export interface SystemStats {
  // Users
  total_users: number;
  active_users: number;
  inactive_users: number;
  admin_users: number;
  viewer_users: number;
  analyst_users: number;
  new_users_today: number;
  new_users_week: number;
  // Properties
  total_properties: number;
  active_properties: number;
  properties_with_3d: number;
  properties_with_video: number;
  avg_price: number;
  total_partners: number;
  active_partners: number;
  // Lists
  districts: { district: string; count: number }[];
  recent_users: { id: string; email: string; role: string; is_active: boolean; created_at: string }[];
}

export async function apiGetAdminStats(): Promise<SystemStats> {
  const { data } = await apiClient.get('/admin/stats');
  return data;
}

export async function apiGetAllUsers(): Promise<UserInfo[]> {
  const { data } = await apiClient.get('/admin/users');
  return data;
}

export async function apiGetUser(userId: string): Promise<UserInfo> {
  const { data } = await apiClient.get(`/admin/users/${userId}`);
  return data;
}

export async function apiUpdateUser(userId: string, updates: { role?: string; is_active?: boolean }): Promise<UserInfo> {
  const { data } = await apiClient.patch(`/admin/users/${userId}`, updates);
  return data;
}

export async function apiDeleteUser(userId: string): Promise<void> {
  await apiClient.delete(`/admin/users/${userId}`);
}

export default apiClient;
