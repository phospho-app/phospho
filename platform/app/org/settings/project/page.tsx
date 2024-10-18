"use client";

import { CopyButton } from "@/components/copy-button";
import { InteractiveDatetime } from "@/components/interactive-datetime";
import CreateProjectDialog from "@/components/projects/create-project-form";
import AlertDialogDeleteProject from "@/components/projects/delete-project-popup";
import DisableAnalytics from "@/components/settings/disable-analytics";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { BriefcaseBusiness, Pencil } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";

export default function Page() {
  const { accessToken } = useUser();
  const [open, setOpen] = useState(false);

  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  if (project_id === null || project_id === undefined) {
    return <>No project selected</>;
  }
  if (selectedProject === null || selectedProject === undefined) {
    return <>Loading...</>;
  }

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold tracking-tight mb-4">
        <div className="flex items-center">
          <div className="flex flex-row items-center">
            <BriefcaseBusiness className="w-6 h-6 mr-2" />
            Project &quot;{selectedProject.project_name}&quot;
          </div>
        </div>
      </h2>
      <div className="mt-4 mb-4 flex-col space-y-4">
        <div className="md:flex flex-auto items-center">
          <div>
            Your project id:{" "}
            <code className="bg-secondary p-1.5">{project_id}</code>
          </div>

          <CopyButton text={project_id} className="ml-2" />
        </div>
        <div className="flex flex-row gap-x-4 ml-2">
          Creation date:{" "}
          <div>
            <InteractiveDatetime timestamp={selectedProject.created_at} />
          </div>
        </div>
        <div>
          <AlertDialog open={open} onOpenChange={setOpen}>
            <AlertDialogTrigger asChild>
              <Button variant="secondary">
                <Pencil className="h-4 w-4 mr-2" />
                Rename project
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="md:w-1/3">
              <CreateProjectDialog
                setOpen={setOpen}
                projectToEdit={selectedProject}
              />
            </AlertDialogContent>
          </AlertDialog>
        </div>
        <DisableAnalytics />
        <div>
          <h2 className="text-2xl font-bold tracking-tight mb-4">
            Danger zone
          </h2>
          <AlertDialogDeleteProject />
        </div>
      </div>
    </div>
  );
}
