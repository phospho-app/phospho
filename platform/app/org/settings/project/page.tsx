"use client";

import AlertDialogDeleteProject from "@/components/projects/delete-project-popup";
import TaskProgress from "@/components/settings/tasks-quota";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { UsageQuota } from "@/models/organizations";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { CopyIcon } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";

export default function Page() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );

  const { accessToken } = useUser();

  const project_id = selectedProject?.id;
  const plan = selectedOrgMetadata?.plan || "hobby";

  const { data: usage }: { data: UsageQuota | null | undefined } = useSWR(
    [`/api/organizations/${selectedOrgId}/usage-quota`, accessToken],
    ([url, token]) => authFetcher(url, token),
  );

  const currentUsage = usage?.current_usage;
  const maxUsage = usage?.max_usage;
  const maxUsageLabel = usage?.max_usage_label;

  if (!project_id) {
    return <>No project selected</>;
  }

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold tracking-tight mb-4">
        Project '{selectedProject.project_name}'
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
          {plan === "pro" && (
            <p>
              You have unlimited usage quota (currently: {currentUsage ?? "..."}{" "}
              logs).
            </p>
          )}
          {plan === "hobby" && (
            <>
              <TaskProgress
                currentValue={currentUsage ?? 0}
                maxValue={maxUsage ?? 1}
              />
              <p>
                Your usage quota is {currentUsage ?? "..."} logs out of{" "}
                {maxUsageLabel ?? "..."}.{" "}
                <Link href="/org/settings/billing" className="underline">
                  Upgrade plan to increase quota
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
