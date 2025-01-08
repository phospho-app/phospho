import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

export function LabelTasksCallout() {
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { accessToken } = useUser();

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const { data: hasLabelledTasks } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/has-enough-labelled-tasks`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
  );

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  return (
    <>
      {hasTasks === true &&
        hasLabelledTasks !== null &&
        selectedOrgMetadata?.plan === "pro" &&
        hasLabelledTasks?.has_enough_labelled_tasks === false && (
          <Card className="bg-secondary">
            <CardHeader>
              <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                <div className="flex flex-row place-items-center">
                  <span className="mr-2">
                    Label{" "}
                    {hasLabelledTasks.enough_labelled_tasks -
                      hasLabelledTasks.currently_labelled_tasks}{" "}
                    messages to improve automatic evaluation
                  </span>
                  <ThumbsDown size={24} /> <ThumbsUp size={24} />
                </div>
              </CardTitle>
              <CardDescription className="flex justify-between flex-col text-muted-foreground space-y-0.5">
                <p>
                  Automatic evaluations are made with your labels. We only found{" "}
                  {hasLabelledTasks.currently_labelled_tasks}/
                  {hasLabelledTasks.enough_labelled_tasks} labels.
                </p>
                <p>
                  Go to a message to label it or automate the process with the
                  API.
                </p>
                <Link
                  href="https://phospho-app.github.io/docs/analytics/user-feedback/"
                  target="_blank"
                >
                  <Button variant="default">Learn more</Button>
                </Link>
              </CardDescription>
            </CardHeader>
          </Card>
        )}
    </>
  );
}
