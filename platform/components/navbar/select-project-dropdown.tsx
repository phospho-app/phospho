"use client";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import useSWR from "swr";

export function SelectProjectButton() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const projects = dataStateStore((state) => state.projects);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const selectedProjectName = selectedProject?.project_name ?? "loading...";

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
      <SelectTrigger className="py-1 h-8">
        <span className="flex mr-1">
          <span className="mr-1">Project</span>
          <SelectValue
            asChild={true}
            children={<div>{selectedProjectName}</div>}
            id={project_id}
          />
        </span>
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
              onClick={(mousEvent) => {
                mousEvent.stopPropagation();
              }}
            >
              {project.project_name}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
