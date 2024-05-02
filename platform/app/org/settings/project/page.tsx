"use client";

import CreateProjectDialog from "@/components/projects/create-project-form";
import AlertDialogDeleteProject from "@/components/projects/delete-project-popup";
import TaskProgress from "@/components/settings/tasks-quota";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { UsageQuota } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { CopyIcon, Pencil } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

export default function Page() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const [open, setOpen] = useState(false);

  const { accessToken } = useUser();

  const plan = selectedOrgMetadata?.plan || "hobby";

  const { data: usage }: { data: UsageQuota | null | undefined } = useSWR(
    [`/api/organizations/${selectedOrgId}/usage-quota`, accessToken],
    ([url, token]) => authFetcher(url, token),
  );

  const currentUsage = usage?.current_usage;
  const maxUsage = usage?.max_usage;

  if (project_id === null || project_id === undefined) {
    return <>No project_id selected</>;
  }
  if (selectedProject === null || selectedProject === undefined) {
    return <>No selected project data</>;
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
              <p>
                You currently have {currentUsage ?? "..."} logs. <br />
              </p>
            </div>
          )}
          {plan === "pro" && (
            <div>
              <p>You currently have {currentUsage ?? "..."} logs.</p>
            </div>
          )}
          {plan === "hobby" && (
            <>
              <TaskProgress
                currentValue={currentUsage ?? 0}
                maxValue={maxUsage ?? 1}
              />
              <p>
                You have currently logged {currentUsage ?? "..."} tasks <br />
                <Link href="/org/settings/billing" className="underline">
                  Add a payment method to enable event detection.
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
