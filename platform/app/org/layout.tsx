"use client";

import InitializeOrganization from "@/components/fetch-data/fetch-org-project";
import Navbar from "@/components/navbar/nav-bar";
import { Sidebar } from "@/components/sidebar/sidebar";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import "@radix-ui/react-dropdown-menu";
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";

export default function OrgLayout({ children }: { children: React.ReactNode }) {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { accessToken, isLoggedIn, loading } = useUser();
  const router = useRouter();

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  if (
    selectedOrgMetadata?.plan === "hobby" &&
    selectedOrgId &&
    process.env.NEXT_PUBLIC_APP_ENV === "production"
  ) {
    // Some orgs are not subject to the blockwall
    const EXEMPTED_ORG_IDS = [
      "13b5f728-21a5-481d-82fa-0241ca0e07b9", // phospho
      "a5724a02-a243-4025-9b34-080f40818a31", // m
    ];
    if (!EXEMPTED_ORG_IDS.includes(selectedOrgId)) {
      // Uncomment this to enable the blockwall
      // router.push("/onboarding/plan?redirect=true");
    }
  }

  if (!isLoggedIn && !loading) {
    router.push("/authenticate");
  }

  return (
    <div className="max-h-screen h-screen">
      <InitializeOrganization />
      <Navbar />
      <Sidebar className="fixed top-12 w-[10rem] hidden md:block" />
      <div className="pt-12 gap-2 w-full px-2 md:pl-[11rem]">
        <div className="flex flex-col py-4">{children}</div>
      </div>
    </div>
  );
}
