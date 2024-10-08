import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
import { useRedirectFunctions, useUser } from "@propelauth/nextjs/client";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function InitializeOrganization() {
  /* 
  This component is responsible for initializing the organization and project
  */

  const { user, loading, accessToken, isLoggedIn } = useUser();
  const { redirectToCreateOrgPage } = useRedirectFunctions();
  const { toast } = useToast();
  const pathname = usePathname();
  const router = useRouter();

  const [redirecting, setRedirecting] = useState(false);

  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );

  useEffect(() => {
    (async () => {
      /*
      This effect is responsible for initializing the organization and project.
      1. If the user is not logged in, redirect to the authenticate page
      2. If the user has no orgs, redirect to the create org page
      3. If the user has orgs, select the first org
      4. Call the init endpoint to initialize the organization and project. If everything is 
        already initialized, this endpoint won't do anything.
      5. If the user is on the home page, redirect to the page returned by the init endpoint
      */
      if (loading) return;
      if (!isLoggedIn) {
        setRedirecting(true);
        router.push("/authenticate");
        return;
      }

      if (user?.getOrgs().length === 0) {
        // User has no orgs. Redirect to create org page
        toast({
          title: "You have no organizations",
          description: "Please create an organization to continue",
        });
        setRedirecting(true);
        redirectToCreateOrgPage();
        return;
      }

      if (user?.orgIdToOrgMemberInfo !== undefined) {
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
            title: `Error initializing organization ${selectedOrgId}`,
            description: init_response.statusText,
          });
          setSelectedOrgId(null);
          return;
        }
        const responseBody = await init_response.json();
        // Set the project id if it is not set
        if (!project_id && responseBody?.selected_project?.id) {
          setproject_id(responseBody.selected_project.id);
        }
        // If redirect to onboarding, set the project_id
        else if (responseBody?.redirect_url?.includes("/onboarding")) {
          setproject_id(responseBody.selected_project.id);
        }
        // Redirect to the page
        if (pathname === "/" && responseBody?.redirect_url && !redirecting) {
          setRedirecting(true);
          router.push(responseBody.redirect_url);
        }
      } catch (error) {
        console.error(
          `Error initializing organization: ${selectedOrgId}`,
          error,
        );
      }
    })();
  }, [
    loading,
    pathname,
    selectedOrgId,
    accessToken,
    isLoggedIn,
    project_id,
    router,
    setproject_id,
    toast,
    redirecting,
    setSelectedOrgId,
    user,
    redirectToCreateOrgPage,
  ]);

  return <></>;
}
