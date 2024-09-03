"use client";

import { SendDataAlertDialog } from "@/components/callouts/import-data";
import CreateProjectDialog from "@/components/projects/create-project-form";
import {
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { AlertDialog } from "@radix-ui/react-alert-dialog";
import { Check, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { usePostHog } from "posthog-js/react";
import * as React from "react";
import useSWR from "swr";

export const OnboardingProgress = () => {
  // This component is used to display the progress of the onboarding process.
  // It is composed of a progress bar and a text label.
  // When clicked, it opens a popover with more information about the onboarding process.

  const [open, setOpen] = React.useState(false);

  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  const { accessToken } = useUser();

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const { data: totalNbTasksData } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/aggregated/tasks`,
          accessToken,
          "total_nb_tasks",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: clusteringsData } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/clusterings`, accessToken, "sidebar"]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
    },
  );

  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;
  const events = selectedProject?.settings?.events || {};
  const current_nb_events = Object.keys(events).length;

  const isProjectPresent = project_id !== null;
  const isEventDefined = current_nb_events > 0;
  const isBillingDefined =
    !selectedOrgMetadata?.plan ||
    selectedOrgMetadata?.plan === "usage_based" ||
    selectedOrgMetadata?.plan === "pro";
  const isDataImported =
    totalNbTasks !== null && totalNbTasks !== undefined && totalNbTasks > 0;

  const isClusteringDone =
    clusteringsData?.clusterings && clusteringsData?.clusterings.length > 0;

  const progress =
    (isProjectPresent ? 25 : 0) +
    (isEventDefined ? 25 : 0) +
    (isBillingDefined ? 25 : 0) +
    (isDataImported ? 25 : 0);

  if (progress === 100) {
    // The onboarding process is complete. Do not display the progress bar.
    return <></>;
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger
        className="text-primary-500 hover:text-green-500 text-sm flex flex-col items-start mx-2"
        onClick={(mouseEvent) => {
          mouseEvent.stopPropagation();
        }}
      >
        Finish onboarding
        <Progress value={progress} />
      </AlertDialogTrigger>
      <AlertDialogContent className="md:h-3/4 md:max-w-1/2">
        <OnboardingProgressPopover
          setOpen={setOpen}
          progress={progress}
          isProjectPresent={isProjectPresent}
          isEventDefined={isEventDefined}
          isBillingDefined={isBillingDefined}
          isDataImported={isDataImported}
          isClusteringDone={isClusteringDone}
        />
      </AlertDialogContent>
    </AlertDialog>
  );
};

const OnboardingTask = ({
  title,
  description,
  onClick,
  completed,
}: {
  title: string;
  description: string;
  onClick: () => void;
  completed: boolean;
}) => {
  if (!completed) {
    return (
      <Card>
        <div className="flex justify-between p-3">
          <div>
            <CardTitle className="text-xl pb-1">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Button
            variant="outline"
            onClick={onClick}
            className="my-auto mr-4 bg-green-500 text-white hover:bg-green-600 hover:text-white"
          >
            Start
          </Button>
        </div>
      </Card>
    );
  }
  return (
    <Card>
      <div className="flex flex-row items-center">
        <Check className="h-6 w-6 ml-2 text-green-500" />
        <CardTitle className="text-lg p-2">{title}</CardTitle>
      </div>
    </Card>
  );
};

const OnboardingProgressPopover = ({
  setOpen,
  progress,
  isProjectPresent,
  isEventDefined,
  isBillingDefined,
  isDataImported,
  isClusteringDone,
}: {
  setOpen: (open: boolean) => void;
  progress: number;
  isProjectPresent: boolean;
  isEventDefined: boolean;
  isBillingDefined: boolean;
  isDataImported: boolean;
  isClusteringDone: boolean;
}) => {
  const [openDataDialog, setOpenDataDialog] = React.useState(false);
  const [openCreateProject, setOpenCreateProject] = React.useState(false);

  const router = useRouter();
  const posthog = usePostHog();
  const toast = useToast();
  const { user, accessToken } = useUser();

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  async function handleCreateProjectClick() {
    setOpenCreateProject(true);
  }

  async function handleEventsClick() {
    router.push("/org/insights/events");
    setOpen(false);
  }

  async function handleBillingClick() {
    try {
      posthog.capture("upgrade_click", {
        propelauthUserId: user?.userId,
      });
      // Call the backend to create a checkout session
      const response = await fetch(
        `/api/organizations/${selectedOrgId}/create-checkout`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            project_id: project_id ? encodeURIComponent(project_id) : null,
          }),
        },
      );
      if (!response.ok) {
        console.log("Error: ", response);
        toast.toast({
          title: "Checkout Error - Please try again later",
          description: `Details: ${response.status} - ${response.statusText}`,
        });
        return;
      }
      const data = await response.json();
      if (data?.error) {
        toast.toast({
          title: "Checkout Error - Please try again later",

          description: data?.error || "Error creating checkout session",
        });
        return;
      }
      const stripeUrl = data?.checkout_url;
      if (stripeUrl) {
        router.push(stripeUrl);
      } else {
        toast.toast({
          title: "Checkout Error - Please try again later",
          description: "Error creating checkout session - no stripe url",
        });
      }
    } catch (error) {
      console.log("Error: ", error);
      toast.toast({
        title: "Checkout Error - Please try again later",
        description: "Error creating checkout session: " + error,
      });
    }
    setOpen(false);
  }

  async function handleImportClick() {
    setOpenDataDialog(true);
  }

  async function handleClusteringClick() {
    router.push("/org/insights/clusters");
    setOpen(false);
  }

  const onboardingTasks = [
    {
      title: "Create your first project",
      description: "",
      onClick: handleCreateProjectClick,
      completed: isProjectPresent,
    },
    {
      title: "Add automatic analytics",
      description: "Detect tags, score text, and classify your data",
      onClick: handleEventsClick,
      completed: isEventDefined,
    },
    {
      title: "Setup a billing method to enable analytics",
      description: "Enable analytics and get 10$ of free credits",
      onClick: handleBillingClick,
      completed: isBillingDefined,
    },
    {
      title: "Import your data",
      description: "Upload a file, connect to a data source, or use an API",
      onClick: handleImportClick,
      completed: isDataImported,
    },
    {
      title: "Run a clustering analysis",
      description: "Discover the hidden meaning in your data",
      onClick: handleClusteringClick,
      completed: isClusteringDone,
    },
  ];

  return (
    <div className="p-4 h-200 w-400">
      <div className="text-primary-500 text-2xl">Onboarding progress</div>
      <div className="mt-2">
        <Progress value={progress} />
      </div>
      <div className="mt-2 text-sm space-y-2 space-x-2">
        <div className="mt-4 text-primary-500">Next steps:</div>
        {/* Display all the uncompleted tasks */}
        {onboardingTasks.map(
          (task) =>
            !task.completed && (
              <OnboardingTask
                title={task.title}
                description={task.description}
                onClick={task.onClick}
                completed={task.completed}
              />
            ),
        )}
      </div>
      <div className="text-sm space-y-2 space-x-2">
        <div className="mt-4 text-primary-500 space-y-4">Completed: </div>
        {/* Display all the completed tasks */}
        {onboardingTasks.map(
          (task) =>
            task.completed && (
              <OnboardingTask
                title={task.title}
                description={task.description}
                onClick={task.onClick}
                completed={task.completed}
              />
            ),
        )}
      </div>
      <div className="absolute right-4 top-4 cursor-pointer">
        <X onClick={() => setOpen(false)} />
      </div>

      <AlertDialog open={openDataDialog}>
        <SendDataAlertDialog setOpen={setOpenDataDialog} />
      </AlertDialog>

      <AlertDialog open={openCreateProject}>
        <AlertDialogContent className="md:max-w-1/4">
          <CreateProjectDialog setOpen={setOpenCreateProject} />
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
