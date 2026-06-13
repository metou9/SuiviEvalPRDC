import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const tokenStore = {
  access: null,
  getRefresh: () => localStorage.getItem("refresh"),
  setRefresh: (t) => localStorage.setItem("refresh", t),
  clearRefresh: () => localStorage.removeItem("refresh"),
  projectId: () => localStorage.getItem("projectId"),
  setProjectId: (id) => localStorage.setItem("projectId", id),
};

const http = axios.create({ baseURL: BASE_URL });

http.interceptors.request.use((config) => {
  if (tokenStore.access) {
    config.headers.Authorization = `Bearer ${tokenStore.access}`;
  }
  const pid = tokenStore.projectId();
  if (pid) {
    config.headers["X-Project-Id"] = pid;
  }
  return config;
});

let onAuthFailure = () => {};
export const setAuthFailureHandler = (fn) => {
  onAuthFailure = fn;
};

// Single refresh-retry on 401 (no queues/polling — sync model).
http.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retried) {
      const refresh = tokenStore.getRefresh();
      if (refresh) {
        original._retried = true;
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh });
          tokenStore.access = data.access;
          if (data.refresh) tokenStore.setRefresh(data.refresh);
          original.headers.Authorization = `Bearer ${data.access}`;
          return http(original);
        } catch (e) {
          tokenStore.clearRefresh();
          onAuthFailure();
        }
      } else {
        onAuthFailure();
      }
    }
    return Promise.reject(error);
  },
);

export default http;
