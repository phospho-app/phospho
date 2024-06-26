"use client";

import CreateProjectDialog from "@/components/projects/create-project-form";
import AlertDialogDeleteProject from "@/components/projects/delete-project-popup";
import DisableAnalytics from "@/components/settings/disable-analytics";
import TaskProgress from "@/components/settings/tasks-quota";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { Project, UsageQuota } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { CopyIcon, Pencil } from "lucide-react";
import Link from "next/link";
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

  const { data: usage }: { data: UsageQuota | null | undefined } = useSWR(
    [`/api/organizations/${selectedOrgId}/usage-quota`, accessToken],
    ([url, token]) => authFetcher(url, token),
  );

  const currentUsage = usage?.current_usage;
  const maxUsage = usage?.max_usage;

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
          <AlertDialog open={open} onOpenChange={setOpen}>
            <AlertDialogTrigger asChild>
              <Pencil className="h-4 w-4 ml-2 hover:text-accent-foreground cursor-pointer" />
            </AlertDialogTrigger>
            <AlertDialogContent className="md:w-1/3">
              <CreateProjectDialog
                setOpen={setOpen}
                projectToEdit={selectedProject}
              />
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </h2>
      <div className="mt-4 mb-4 flex-col space-y-8">
        <div className="md:flex flex-auto items-center mb-4">
          <div>Your project id: {project_id}</div>
          <Button
            variant="outline"
            className="ml-2"
            size="icon"
            onClick={() => {
              navigator.clipboard.writeText(project_id);
            }}
          >
            <CopyIcon size="16" />
          </Button>
        </div>
        <div>
          <Link
            href={`${process.env.NEXT_PUBLIC_AUTH_URL}/org/api_keys/${selectedOrgId}`}
          >
            <Button variant="default" className="w-80 mr-8">
              Get Phospho API key
            </Button>
          </Link>
          <AlertDialogDeleteProject />
        </div>
        <div>
          {plan === "usage_based" && (
            <div>
              <p>You have currently run {currentUsage ?? "..."} detections.</p>
            </div>
          )}
          {plan === "pro" && (
            <div>
              <p>You have currently run {currentUsage ?? "..."} detections.</p>
            </div>
          )}
          {plan === "hobby" && (
            <>
              <TaskProgress
                currentValue={currentUsage ?? 0}
                maxValue={maxUsage ?? 1}
              />
              <p>
                You have currently run {currentUsage ?? "..."}/{maxUsage}{" "}
                detections.
              </p>
              <Link href="/org/settings/billing" className="underline">
                Add a payment method to enable more detections.
              </Link>
            </>
          )}
        </div>
        <DisableAnalytics />
      </div>
    </div>
  );
}
