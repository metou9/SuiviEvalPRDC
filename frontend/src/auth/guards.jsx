import { Navigate } from "react-router-dom";

import { useAuth } from "./AuthProvider.jsx";

export function RequireAuth({ children }) {
  const { me, ready } = useAuth();
  if (!ready) return null;
  if (!me) return <Navigate to="/login" replace />;
  return children;
}

export function RequireCapability({ cap, children }) {
  const { hasCapability } = useAuth();
  if (!hasCapability(cap)) {
    return <div className="p-4">Accès non autorisé.</div>;
  }
  return children;
}
