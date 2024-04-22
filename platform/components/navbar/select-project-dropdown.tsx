"use client";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { dataStateStore, navigationStateStore } from "@/store/store";

import CreateProjectButton from "./create-project-button";

export function SelectProjectButton() {
  // Zustand state management
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const projects = dataStateStore((state) => state.projects);

  const selectedProjectName = selectedProject?.project_name ?? "loading...";
  const setHasTasks = dataStateStore((state) => state.setHasTasks);
  const setHasSessions = dataStateStore((state) => state.setHasSessions);

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
      }
    }
  };

  if (!project_id) {
    return <></>;
  }

  return (
    <Select
      onValueChange={handleValueChange}
      defaultValue={selectedProjectName}
    >
      <SelectTrigger>
        <span className="mr-1">Project</span>
        <SelectValue
          asChild={true}
          children={<div>{selectedProjectName}</div>}
          id={project_id}
        />
      </SelectTrigger>
      <SelectContent
        position="popper"
        className="overflow-y-auto max-h-[40rem]"
      >
        <SelectGroup>
          <SelectLabel>Projects ({`${projects?.length}`})</SelectLabel>
          {projects.map((project) => (
            <SelectItem
              key={project.id}
              value={project.project_name}
              // onSelect={() => handleProjectChange(project.id)}
            >
              {project.project_name}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
