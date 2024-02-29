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
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { useState } from "react";

const AlertDialogDeleteProject = () => {
  const { user, loading, accessToken } = useUser();

  const [clicked, setClicked] = useState(false);

  // Zustand state management
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const setSelectedProject = navigationStateStore(
    (state) => state.setSelectedProject,
  );
  const projects = dataStateStore((state) => state.projects);
  const setProjects = dataStateStore((state) => state.setProjects);

  const router = useRouter();

  return (
    selectedProject && (
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="destructive" className="justify-start">
            Delete project
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete the project "{selectedProject.project_name}"?
            </AlertDialogTitle>
            <AlertDialogDescription>
              <div className="mt-4">Are you sure? No undo.</div>
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
                  console.log("delete project");
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
                    console.log("Project deleted");
                    const filteredProjects = projects.filter(
                      (project) => project.id !== selectedProject.id,
                    );
                    setProjects(filteredProjects);
                    setSelectedProject(filteredProjects[0]);
                    setClicked(false);
                    router.push("/org/transcripts/tasks");
                  } else {
                    console.log("Project deletion failed");
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
