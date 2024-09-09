import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import useSWR from "swr";

export default function FetchOrgProject() {
  // This module fetch top-level settings for the org and the project

  const { user, loading, accessToken, isLoggedIn } = useUser();
  const { toast } = useToast();
  const pathname = usePathname();
  const router = useRouter();

  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setSelectOrgMetadata = dataStateStore(
    (state) => state.setSelectOrgMetadata,
  );

  useEffect(() => {
    // Initialize the org if it has no projects
    // Creates a project if it has no projects
    // Otherwise, select the first project
    (async () => {
      if (loading) return;

      if (!loading && !isLoggedIn) {
        router.push("/authenticate");
      }

      if (!selectedOrgId) return;

      try {
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
        if (init_response.status !== 200) {
          toast({
            title: "Error initializing organization",
            description: "Please try again later",
          });
          return;
        }
        const responseBody = await init_response.json();
        // Set the project id if it is not set
        if (!project_id && responseBody?.selected_project?.id) {
          setproject_id(responseBody.selected_project.id);
        }
        // Redirect to the page
        if (pathname === "/") {
          router.push(responseBody?.redirect_url);
        }
      } catch (error) {
        console.error("Error initializing organization:", error);
      }
    })();
  }, [
    selectedOrgId,
    loading,
    accessToken,
    isLoggedIn,
    pathname,
    project_id,
    router,
    setproject_id,
    toast,
  ]);

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
  const { data: fetchedOrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  if (fetchedOrgMetadata) {
    setSelectOrgMetadata(fetchedOrgMetadata);
  }

  return <></>;
}
