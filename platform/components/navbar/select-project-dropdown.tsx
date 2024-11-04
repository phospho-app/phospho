"use client";

import { Input } from "@/components/ui/input";
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
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { MagnifyingGlassIcon } from "@radix-ui/react-icons";
import { BriefcaseBusiness } from "lucide-react";
import { useEffect, useState } from "react";
import useSWR from "swr";

export function SelectProjectButton() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const [projectNameSearch, setProjectNameSearch] = useState<string | null>(
    null,
  );

  const {
    data: projectsData,
  }: {
    data: { projects: Project[] } | null | undefined;
  } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/projects`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const projects = projectsData?.projects;

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  useEffect(() => {
    setProjectNameSearch(null);
  }, [selectedOrgId]);

  const selectedProjectId = project_id ?? "loading...";
  const selectedProjectName = selectedProject?.project_name ?? "loading...";

  if (projects === null || projects === undefined) {
    return <></>;
  }

  const handleValueChange = (selected_project_id: string) => {
    if (selected_project_id != "project_id") {
      setproject_id(selected_project_id);
    }
  };

  return (
    <Select onValueChange={handleValueChange} value={selectedProjectId}>
      <SelectTrigger className="py-1 h-8">
        <span className="flex space-x-1">
          <div className="flex items-center">Project</div>
          <SelectValue asChild={true} id={selectedProjectId}>
            <div>{selectedProjectName}</div>
          </SelectValue>
        </span>
      </SelectTrigger>
      <SelectContent position="popper">
        <SelectGroup>
          <SelectLabel>
            <div className="flex flex-row items-center">
              <BriefcaseBusiness className="w-4 h-4 mr-1" />
              Projects ({`${projects?.length}`})
            </div>
          </SelectLabel>
          <SelectLabel>
            {projects.length > 15 && (
              <div className="flex flex-row gap-x-2 items-center">
                <MagnifyingGlassIcon className="size-4" />
                <Input
                  placeholder="Search for project name"
                  className=""
                  value={projectNameSearch ?? ""}
                  onChange={(e) => {
                    setProjectNameSearch(e.target.value);
                  }}
                />
              </div>
            )}
          </SelectLabel>
        </SelectGroup>
        <SelectGroup className="overflow-y-auto max-h-[40rem]">
          {projects
            .filter((project) =>
              !projectNameSearch
                ? true
                : project.project_name
                    .toLowerCase()
                    .startsWith(projectNameSearch.toLowerCase()),
            )
            .map((project) => (
              <SelectItem
                key={project.id}
                value={project.id}
                onClick={(mouseEvent) => {
                  mouseEvent.stopPropagation();
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
