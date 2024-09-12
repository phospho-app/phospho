"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Trash } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";

const AlertDialogDeleteProject = () => {
  const router = useRouter();
  const { accessToken } = useUser();
  const { mutate } = useSWRConfig();

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const [clicked, setClicked] = useState(false);

  const {
    data: projectsData,
    mutate: setProjects,
  }: {
    data: { projects: Project[] } | null | undefined;
    mutate: (data: { projects: Project[] }) => void;
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

  return (
    selectedProject && (
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="destructive" className="justify-start">
            <Trash className="w-4 h-4 mr-2" />
            Delete project
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent className="md:w-1/3">
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete the project &quot;{selectedProject.project_name}&quot;?
            </AlertDialogTitle>
            <AlertDialogDescription className="mt-4">
              Are you sure? No undo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            {clicked && (
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
            )}
            {!clicked && (
              <AlertDialogAction
                onClick={async () => {
                  setClicked(true);
                  if (!projects) return;
                  // Don't delete the project if only 1 project is left
                  if (projects.length === 1) return;

                  const response = await fetch(
                    `/api/projects/${selectedProject.id}/delete`,
                    {
                      method: "DELETE",
                      headers: {
                        Authorization: "Bearer " + accessToken,
                        "Content-Type": "application/json",
                      },
                    },
                  );
                  const response_json = await response.json();
                  // Update the list of projects and the selected project
                  if (response_json.id === selectedProject.id) {
                    const filteredProjects = projects.filter(
                      (project) => project.id !== selectedProject.id,
                    );
                    // Mutate the projects list
                    mutate(
                      [
                        `/api/organizations/${selectedOrgId}/projects`,
                        accessToken,
                      ],
                      async () => {
                        return { projects: filteredProjects };
                      },
                    );
                    setProjects({ projects: filteredProjects });
                    setproject_id(filteredProjects[0].id);
                    setClicked(false);
                    router.push("/org/transcripts/tasks");
                  } else {
                    setClicked(false);
                  }
                }}
              >
                Delete project
              </AlertDialogAction>
            )}
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    )
  );
};

export default AlertDialogDeleteProject;
