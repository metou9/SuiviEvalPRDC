import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { createElement } from "react";

import { auth as authApi } from "../services/api.js";
import { setAuthFailureHandler, tokenStore } from "../services/http.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [me, setMe] = useState(null);
  const [ready, setReady] = useState(false);

  const loadMe = async () => {
    const data = await authApi.me();
    if (!tokenStore.projectId() && data.current_project) {
      tokenStore.setProjectId(String(data.current_project));
    }
    setMe(data);
    return data;
  };

  const logout = () => {
    tokenStore.access = null;
    tokenStore.clearRefresh();
    setMe(null);
  };

  useEffect(() => {
    setAuthFailureHandler(() => logout());
    (async () => {
      const refresh = tokenStore.getRefresh();
      if (refresh) {
        try {
          await loadMe();
        } catch (e) {
          logout();
        }
      }
      setReady(true);
    })();
  }, []);

  const login = async (username, password) => {
    const data = await authApi.token(username, password);
    tokenStore.access = data.access;
    tokenStore.setRefresh(data.refresh);
    return loadMe();
  };

  const setCurrentProject = async (id) => {
    tokenStore.setProjectId(String(id));
    await loadMe();
  };

  const hasCapability = (cap) => {
    if (!me) return false;
    if (me.is_superuser || (me.capabilities || []).includes("*")) return true;
    return (me.capabilities || []).includes(cap);
  };

  const value = { me, ready, login, logout, setCurrentProject, hasCapability, reload: loadMe };
  return createElement(AuthContext.Provider, { value }, children);
}

export const useAuth = () => useContext(AuthContext);
