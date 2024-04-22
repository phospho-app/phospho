"use client";

import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import useSWR from "swr";

function FetchHasTasksSessions() {
  // This module data relates to the tasks and sessions of the project
  const { accessToken } = useUser();
  const { toast } = useToast();

  const project_id = navigationStateStore((state) => state.project_id);
  const hasLabelledTasks = dataStateStore((state) => state.hasLabelledTasks);
  const setHasSessions = dataStateStore((state) => state.setHasSessions);
  const setHasTasks = dataStateStore((state) => state.setHasTasks);
  const setHasLabelledTasks = dataStateStore(
    (state) => state.setHasLabelledTasks,
  );

  const setSelectedProject = dataStateStore(
    (state) => state.setSelectedProject,
  );

  console.log("Rendering FetchHasTasksSessions");

  // Fetch the has session
  const { data: hasSessionData } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/has-sessions`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
  );
  if (hasSessionData) {
    setHasSessions(hasSessionData.has_sessions);
  }

  // Fetch has tasks
  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
  );
  if (hasTasksData) {
    setHasTasks(hasTasksData.has_tasks);
  }

  // Fetch has enough labelled tasks
  const { data: hasLabelledTasksData } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/has-enough-labelled-tasks`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
  );
  if (hasLabelledTasksData) {
    setHasLabelledTasks(hasLabelledTasksData);
  }

  // Display a toast if the user has labelled enough tasks
  if (hasLabelledTasksData?.project_id === hasLabelledTasks?.project_id) {
    if (
      hasLabelledTasksData?.has_enough_labelled_tasks === true &&
      hasLabelledTasks?.has_enough_labelled_tasks === false
    ) {
      toast({
        title: `You labelled ${hasLabelledTasksData?.enough_labelled_tasks} tasks 🎉`,
        description: `Keep labelling to improve automatic evaluations.`,
      });
    }
  }

  // Fetch the selected project from the server. This is useful when the user
  // change the settings
  const { data: fetchedProject } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  if (fetchedProject) {
    console.log("Updating fetchedProject:", fetchedProject);
    setSelectedProject(fetchedProject);
  }

  return <></>;
}

export default FetchHasTasksSessions;
export { FetchHasTasksSessions };
