import { Dropdown } from "primereact/dropdown";

import { useAuth } from "../auth/AuthProvider.jsx";

export default function ProjectSwitcher() {
  const { me, setCurrentProject } = useAuth();
  if (!me) return null;
  const options = (me.projects || []).map((p) => ({ label: p.name, value: p.project }));
  if (options.length <= 1) {
    return <span className="fw-semibold">{options[0]?.label}</span>;
  }
  return (
    <Dropdown
      value={me.current_project}
      options={options}
      onChange={(e) => setCurrentProject(e.value)}
      className="p-inputtext-sm"
    />
  );
}
