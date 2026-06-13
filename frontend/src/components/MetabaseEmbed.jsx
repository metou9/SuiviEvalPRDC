import { useEffect, useState } from "react";

import { metabase } from "../services/api.js";

// Fetches a signed embed URL from the backend then renders a responsive iframe.
// Re-fetches whenever the dashboard id or filters change (project is locked server-side).
export default function MetabaseEmbed({ dashboard, filters = {} }) {
  const [url, setUrl] = useState(null);
  const [error, setError] = useState(false);
  const filterKey = JSON.stringify(filters);

  useEffect(() => {
    let active = true;
    if (!dashboard) return;
    setError(false);
    metabase
      .embed(dashboard, filters)
      .then((data) => active && setUrl(data.iframe_url))
      .catch(() => active && setError(true));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dashboard, filterKey]);

  if (!dashboard) {
    return (
      <div className="text-muted p-3 border rounded bg-light">
        Tableau de bord Metabase non configuré (VITE_MB_DASHBOARD_*).
      </div>
    );
  }
  if (error) return <div className="text-danger p-3">Erreur de chargement du tableau.</div>;
  if (!url) return <div className="p-3">Chargement du tableau…</div>;

  return (
    <div className="metabase-frame">
      <iframe title={`metabase-${dashboard}`} src={url} allowTransparency />
    </div>
  );
}
