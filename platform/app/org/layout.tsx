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
      "bb46a507-19db-4e11-bf26-6bd7cdc8dcdd", // e
      "a5724a02-a243-4025-9b34-080f40818a31", // m
      "144df1a7-40f6-4c8d-a0a2-9ed010c1a142", // v
      "3bf3f4b0-2ef7-47f7-a043-d96e9f5a3d7e", // st
      "8e530a71-8739-450a-844a-5a6430067f9a", // y
      "2fdbcf01-eb52-4747-bb14-b66621973e8f", // sa
      "5a3d67ab-231c-4ad1-adba-84b6842668ad", // sa (a)
      "7e8f6db2-3b6b-4bf6-84ee-3f226b81e43d", // di
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
