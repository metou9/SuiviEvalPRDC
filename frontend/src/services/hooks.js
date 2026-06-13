import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api.js";
import { tokenStore } from "./http.js";

// Generic list hook keyed by resource + project + params.
export function useList(resourceName, params = {}) {
  const pid = tokenStore.projectId();
  return useQuery({
    queryKey: [resourceName, pid, params],
    queryFn: () => api[resourceName].list(params),
  });
}

export function useItem(resourceName, id, params = {}) {
  const pid = tokenStore.projectId();
  return useQuery({
    queryKey: [resourceName, pid, "item", id, params],
    queryFn: () => api[resourceName].get(id, params),
    enabled: !!id,
  });
}

export function useSave(resourceName) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      id ? api[resourceName].update(id, body) : api[resourceName].create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [resourceName] }),
  });
}

export function useRemove(resourceName) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => api[resourceName].remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [resourceName] }),
  });
}

export function useTransition(resourceName) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action, comment }) => api[resourceName].transition(id, action, comment),
    onSuccess: () => qc.invalidateQueries({ queryKey: [resourceName] }),
  });
}
