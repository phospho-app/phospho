"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import FullPageLoader from "@/components/full-page-loader";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import React from "react";

const Page: React.FC = () => {
  const { user, loading, accessToken } = useUser();

  // State Variables
  const project_id = navigationStateStore((state) => state.project_id);
  const projects = dataStateStore((state) => state.projects);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const router = useRouter();

  if (process.env.NODE_ENV === "production") {
    console.log = function () {};
  }

  if (!loading && !user) {
    router.push("/authenticate");
  }

  // If no project, redirect to the onboarding page
  if (selectedOrgId && user && projects !== null && projects.length === 0) {
    router.push("/onboarding/", { scroll: false });
  }

  // Once connected, redirect to the dashboard
  if (projects && projects.length > 0 && project_id) {
    router.push("/org/transcripts/tasks", { scroll: false });
  }

  return (
    <>
      <FetchOrgProject />
      <FullPageLoader />
    </>
  );
};

export default Page;
