"use client";

import CreateProjectDialog from "@/components/projects/CreateProjectForm";
import AlertDialogDeleteProject from "@/components/projects/DeleteProjectPopup";
import DisableAnalytics from "@/components/settings/DisableAnalytics";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/AlertDialog";
import { Button } from "@/components/ui/Button";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { BriefcaseBusiness, CopyIcon, Pencil } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";

export default function Page() {
  const { accessToken } = useUser();
  const [open, setOpen] = useState(false);

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const plan = selectedOrgMetadata?.plan || "hobby";

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
            Project "{selectedProject.project_name}"
          </div>
        </div>
      </h2>
      <div className="mt-4 mb-4 flex-col space-y-4">
        <div className="md:flex flex-auto items-center">
          <div>
            Your project id:{" "}
            <code className="bg-secondary p-1.5">{project_id}</code>
          </div>
          <Button
            variant="outline"
            className="ml-2"
            size="icon"
            onClick={() => {
              navigator.clipboard.writeText(project_id);
            }}
          >
            <CopyIcon className="w-3 h-3" />
          </Button>
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
