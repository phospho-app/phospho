"use client";

import CreateProjectDialog from "@/components/projects/create-project-form";
import AlertDialogDeleteProject from "@/components/projects/delete-project-popup";
import DisableAnalytics from "@/components/settings/disable-analytics";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { CopyIcon, Pencil } from "lucide-react";
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
        <div className="flex items-baseline">
          Project "{selectedProject.project_name}"
          <HoverCard openDelay={0} closeDelay={0}>
            <AlertDialog open={open} onOpenChange={setOpen}>
              <AlertDialogTrigger asChild>
                <HoverCardTrigger asChild>
                  <Button variant="ghost" size="icon" className="ml-2">
                    <Pencil className="h-4 w-4" />
                  </Button>
                </HoverCardTrigger>
              </AlertDialogTrigger>
              <AlertDialogContent className="md:w-1/3">
                <CreateProjectDialog
                  setOpen={setOpen}
                  projectToEdit={selectedProject}
                />
              </AlertDialogContent>
            </AlertDialog>
            <HoverCardContent className="text-xs font-normal text-background bg-foreground m-0">
              <span>Rename project</span>
            </HoverCardContent>
          </HoverCard>
        </div>
      </h2>
      <div className="mt-4 mb-4 flex-col space-y-8">
        <div className="md:flex flex-auto items-center mb-4">
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
