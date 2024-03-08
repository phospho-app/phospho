import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/project";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useEffect } from "react";
import useSWR from "swr";

import { useToast } from "../ui/use-toast";

export default function FetchOrgProject() {
  // This module fetch top-level settings for the org and the project

  const { user, loading, accessToken } = useUser();
  const { toast } = useToast();

  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const setSelectedProject = navigationStateStore(
    (state) => state.setSelectedProject,
  );
  const projects = dataStateStore((state) => state.projects);
  const setProjects = dataStateStore((state) => state.setProjects);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setUniqueEventNames = dataStateStore(
    (state) => state.setUniqueEventNames,
  );
  const setSelectOrgMetadata = dataStateStore(
    (state) => state.setSelectOrgMetadata,
  );

  useEffect(() => {
    // Initialize the org if it has no project
    (async () => {
      if (!user) return;
      if (!selectedOrgId) return;
      if (!projects) return;

      try {
        if (projects.length > 0) {
          setProjects(projects);
          console.log("selectedProject:", selectedProject);
          if (
            (selectedProject === null || selectedProject === undefined) &&
            projects?.length > 0
          ) {
            // Auto select the first project
            const selected_project = projects[0];
            setSelectedProject(selected_project);
            // Set the unique event names
            if (selected_project.settings?.events) {
              setUniqueEventNames(
                Object.keys(selected_project.settings.events),
              );
            } else {
              setUniqueEventNames([]);
            }
          }
        } else {
          console.log("This org has no project yet");
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
          setProjects([]);
        }
      } catch (error) {
        console.error("Error fetching repositories:", error);
      }
    })();
  }, [selectedOrgId, projects?.length, loading]);

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
  if (orgMetadataError) {
    toast({
      title: "Error fetching org metadata",
      description: `Details: ${orgMetadataError}`,
    });
  }
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
  }
  if (fetchedProjectsData?.projects !== undefined) {
    setProjects(fetchedProjectsData?.projects);
  }

  const fetchedProjectIds = fetchedProjectsData?.projects?.map(
    (project) => project.id,
  );
  if (
    // If selected project is not in the fetched projects, select the first project
    (selectedProject &&
      fetchedProjectsData?.projects !== undefined &&
      fetchedProjectIds !== undefined &&
      fetchedProjectIds?.length > 0 &&
      !fetchedProjectIds.includes(selectedProject?.id)) ||
    // If no project is selected, select the first project
    ((selectedProject === null || selectedProject === undefined) &&
      fetchedProjectsData?.projects !== undefined &&
      fetchedProjectsData?.projects.length > 0)
  ) {
    const selected_project = fetchedProjectsData?.projects[0];
    setSelectedProject(selected_project);
    if (selected_project.settings?.events) {
      setUniqueEventNames(Object.keys(selected_project.settings.events));
    } else {
      setUniqueEventNames([]);
    }
  }

  // Fetch the selected project from the server. This is useful when the user
  // change the settings
  const { data: fetchedProject } = useSWR(
    selectedProject?.id
      ? [
          `/api/projects/${selectedProject?.id}`,
          accessToken,
          selectedProject?.settings?.events?.length,
        ]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
  );
  if (
    fetchedProject &&
    (selectedProject === null ||
      selectedProject === undefined ||
      fetchedProject.id !== selectedProject.id ||
      fetchedProject.settings?.events?.length !==
        selectedProject.settings?.events?.length)
  ) {
    console.log("Updating fetchedProject:", fetchedProject);
    setSelectedProject(fetchedProject);
  }

  return <></>;
}
