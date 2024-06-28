import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useEffect } from "react";
import useSWR from "swr";

import { useToast } from "../ui/use-toast";

export default function FetchOrgProject() {
  // This module fetch top-level settings for the org and the project

  const { user, loading, accessToken } = useUser();
  const { toast } = useToast();

  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const projects = dataStateStore((state) => state.projects);
  const setProjects = dataStateStore((state) => state.setProjects);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setSelectOrgMetadata = dataStateStore(
    (state) => state.setSelectOrgMetadata,
  );

  console.log("Rendering FetchOrgProject");

  useEffect(() => {
    // Initialize the org if it has no project
    // This is called the first time the user logs in,
    // before onboarding
    (async () => {
      if (!accessToken) return;
      if (!selectedOrgId) return;
      if (!projects) return;

      try {
        if (projects.length > 0) {
          console.log("project_id:", project_id);
          if (
            (project_id === null || project_id === undefined) &&
            projects?.length > 0
          ) {
            // Auto select the first project
            const selected_project = projects[0];
            setproject_id(selected_project.id);
          }
        } else {
          console.log("This org has no project yet. Initializing...");
          const init_response = await fetch(
            `/api/organizations/${selectedOrgId}/init`,
            {
              method: "POST",
              headers: {
                Authorization: "Bearer " + accessToken,
                "Content-Type": "application/json",
              },
            },
          );
        }
      } catch (error) {
        console.error("Error fetching repositories:", error);
      }
    })();
  }, [selectedOrgId, projects?.length, accessToken]);

  if (user && !loading && user.orgIdToOrgMemberInfo !== undefined) {
    const userOrgIds = Object.keys(user.orgIdToOrgMemberInfo);
    if (selectedOrgId === undefined || selectedOrgId === null) {
      // Put the first org id in the state
      // Get it from the user object, in the maping orgIdToOrgMemberInfo
      const orgId = userOrgIds[0];
      setSelectedOrgId(orgId);
    }
    // If currently selected org is not in the user's orgs, select the first org
    else if (!userOrgIds.includes(selectedOrgId)) {
      const orgId = userOrgIds[0];
      setSelectedOrgId(orgId);
    }
  }

  // Fetch the org metadata
  const { data: fetchedOrgMetadata, error: orgMetadataError } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
  );
  if (fetchedOrgMetadata) {
    setSelectOrgMetadata(fetchedOrgMetadata);
  }

  // Fetch the projects
  const {
    data: fetchedProjectsData,
    error: projectFetchingError,
  }: {
    data: { projects: Project[] } | null | undefined;
    error: any;
  } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/projects`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
  );
  if (projectFetchingError) {
    toast({
      title: "Error fetching projects",
      description: `Details: ${projectFetchingError}`,
    });
    return <></>;
  }
  if (fetchedProjectsData?.projects !== undefined) {
    setProjects(fetchedProjectsData?.projects);
  }

  const fetchedProjectIds = fetchedProjectsData?.projects?.map(
    (project) => project.id,
  );
  if (
    // If selected project is not in the fetched projects, select the first project
    (project_id &&
      fetchedProjectsData?.projects !== undefined &&
      fetchedProjectIds !== undefined &&
      fetchedProjectIds?.length > 0 &&
      !fetchedProjectIds.includes(project_id)) ||
    // If no project is selected, select the first project
    ((project_id === null || project_id === undefined) &&
      fetchedProjectsData?.projects !== undefined &&
      fetchedProjectsData?.projects.length > 0)
  ) {
    const selected_project = fetchedProjectsData?.projects[0];
    setproject_id(selected_project.id);
  }

  return <></>;
}
