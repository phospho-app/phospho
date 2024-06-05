"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import FetchHasTasksSessions from "@/components/fetch-data/fetch-tasks-sessions";
import Navbar from "@/components/navbar/nav-bar";
import { Sidebar } from "@/components/sidebar";
import { dataStateStore, navigationStateStore } from "@/store/store";
import "@radix-ui/react-dropdown-menu";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

export default function OrgLayout({ children }: { children: React.ReactNode }) {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const router = useRouter();

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

  return (
    <section>
      <FetchOrgProject />
      <FetchHasTasksSessions />
      <div className="max-h-screen h-screen overflow-hidden">
        <div className="h-full">
          <Navbar />
          <div className="grid grid-cols-8 gap-2 w-full h-full">
            <div className="hidden md:block">
              <Sidebar />
            </div>
            <div className="space-y-4 px-4 col-span-8 md:col-span-7 overflow-y-auto py-4">
              {children}
              <div className="h-20"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
