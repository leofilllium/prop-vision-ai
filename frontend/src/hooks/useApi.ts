/**
 * React Query hooks for data fetching.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { fetchProperties, fetchProperty, searchProperties, fetchComfortScores, fetchDashboard, apiGetAdminStats, apiGetAllUsers, apiUpdateUser, apiDeleteUser } from '../api/client';

export function useProperties(params?: Parameters<typeof fetchProperties>[0]) {
  return useQuery({
    queryKey: ['properties', params],
    queryFn: () => fetchProperties(params),
  });
}

export function useProperty(id: string | null) {
  return useQuery({
    queryKey: ['property', id],
    queryFn: () => fetchProperty(id!),
    enabled: !!id,
  });
}

export function useSearch() {
  return useMutation({
    mutationFn: (query: string) => searchProperties(query),
  });
}

export function useComfortScores(propertyId: string | null) {
  return useQuery({
    queryKey: ['comfort', propertyId],
    queryFn: () => fetchComfortScores(propertyId!),
    enabled: !!propertyId,
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useAdminStats(enabled = true) {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: apiGetAdminStats,
    enabled,
    refetchInterval: enabled ? 30000 : false,
    retry: false,
  });
}

export function useAllUsers(enabled = true) {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: apiGetAllUsers,
    enabled,
    refetchInterval: enabled ? 30000 : false,
    retry: false,
  });
}

export function useUpdateUser() {
  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: { role?: string; is_active?: boolean } }) =>
      apiUpdateUser(userId, updates),
  });
}

export function useDeleteUser() {
  return useMutation({
    mutationFn: (userId: string) => apiDeleteUser(userId),
  });
}
