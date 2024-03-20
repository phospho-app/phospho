"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
// zustand state management
import { dataStateStore, navigationStateStore } from "@/store/store";

export function SelectProjectButton() {
  // Zustand state management
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const projects = dataStateStore((state) => state.projects);

  const selectedProjectName = selectedProject?.project_name ?? "loading...";
  const setHasTasks = dataStateStore((state) => state.setHasTasks);
  const setHasSessions = dataStateStore((state) => state.setHasSessions);
  const setUniqueEventNames = dataStateStore(
    (state) => state.setUniqueEventNames,
  );

  if (projects === null) {
    return <></>;
  }

  const handleValueChange = (project_name: string) => {
    console.log("Selected Project in selectbutton:", project_name);
    // Match the selected project name with the project in the projects array
    const selectedProjectInForm = projects.find(
      (project) => project.project_name === project_name,
    );

    if (selectedProjectInForm) {
      if (selectedProjectInForm.id != "project_id") {
        setHasTasks(null);
        setHasSessions(null);
        setproject_id(selectedProjectInForm.id);
        if (selectedProjectInForm.settings?.events) {
          setUniqueEventNames(
            Object.keys(selectedProjectInForm.settings.events),
          );
        } else {
          setUniqueEventNames([]);
        }
      }
    }
  };

  return (
    <div className="px-3 py-2">
      <Select
        onValueChange={handleValueChange}
        defaultValue={selectedProjectName}
      >
        <SelectTrigger>
          <SelectValue
            asChild={true}
            children={<div>{selectedProjectName}</div>}
            id={selectedProject?.id}
          />
        </SelectTrigger>
        <SelectContent position="popper">
          {projects.map((project) => (
            <SelectItem
              key={project.id}
              value={project.project_name}
              // onSelect={() => handleProjectChange(project.id)}
            >
              {project.project_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
