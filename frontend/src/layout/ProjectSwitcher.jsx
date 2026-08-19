import { Dropdown } from "primereact/dropdown";

import { useAuth } from "../auth/AuthProvider.jsx";


export default function ProjectSwitcher() {
  const {
    me,
    setCurrentProject,
  } = useAuth();


  if (!me) {
    return null;
  }


  const options = (me.projects || []).map((project) => ({
    label: project.name,
    value: project.project,
  }));


  const currentProject =
    options.find(
      (option) =>
        option.value === me.current_project
    ) ||
    options[0];


  if (!currentProject) {
    return null;
  }


  /*
   * Un seul projet :
   * affichage institutionnel propre sans dropdown inutile.
   */

  if (options.length <= 1) {
    return (
      <div className="project-switcher-single">

        <div className="project-switcher-icon">
          <i className="pi pi-briefcase" />
        </div>

        <div className="project-switcher-info">
          <span>
            Projet courant
          </span>

          <strong>
            {currentProject.label}
          </strong>
        </div>

      </div>
    );
  }


  /*
   * Plusieurs projets :
   * dropdown conservant exactement la logique existante.
   */

  const valueTemplate = (option) => {
    const selected =
      option ||
      currentProject;

    return (
      <div className="project-switcher-value">
        <div className="project-switcher-icon">
          <i className="pi pi-briefcase" />
        </div>

        <div className="project-switcher-info">
          <span>
            Projet courant
          </span>

          <strong>
            {selected?.label || ""}
          </strong>
        </div>
      </div>
    );
  };


  const itemTemplate = (option) => (
    <div className="project-switcher-option">
      <i className="pi pi-briefcase" />

      <span>
        {option.label}
      </span>
    </div>
  );


  return (
    <Dropdown
      value={me.current_project}
      options={options}
      onChange={(event) =>
        setCurrentProject(event.value)
      }
      valueTemplate={valueTemplate}
      itemTemplate={itemTemplate}
      className="project-switcher-dropdown"
      panelClassName="project-switcher-panel"
    />
  );
}