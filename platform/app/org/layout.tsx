"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import FetchHasTasksSessions from "@/components/fetch-data/fetch-tasks-sessions";
import Navbar from "@/components/navbar/nav-bar";
import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { LucideSmartphone } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

export default function OrgLayout({ children }: { children: React.ReactNode }) {
  const [isMobile, setIsMobile] = useState(false);
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

  useEffect(() => {
    const handleResize = () => {
      // Update the state based on the window width
      setIsMobile(window.innerWidth < 600); // Adjust the threshold according to your design
    };

    // Set the initial state
    handleResize();

    // Add event listener for window resize
    window.addEventListener("resize", handleResize);

    // Clean up the event listener when the component is unmounted
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  if (isMobile) {
    return (
      <>
        <div className="flex flex-col items-center justify-center h-screen">
          <h2 className="text-3xl font-semibold text-green-500 mb-4">
            phospho
          </h2>
          <div className="text-center space-y-4 py-4 px-10 overflow-y-auto max-h-[calc(100vh-4rem)]">
            <div className="text-3xl font-bold mb-10 flex items-center justify-center">
              <LucideSmartphone size={30} className="mr-2" />
              <p>Your screen is too narrow</p>
            </div>
            <p className="text-xl">
              Switch your mobile browser to desktop mode or use a computer to
              access phospho
            </p>
            <div className="text-gray-500 items-center flex flex-col">
              <p>Are you a frontend developer?</p>
              <div>
                <Link href="mailto:contact@phospho.app">
                  <Button variant="outline">Help us out!</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <section>
      <FetchOrgProject />
      <FetchHasTasksSessions />
      <div className="max-h-screen h-screen overflow-hidden">
        <div className="h-full">
          <div className="w-full">
            <Navbar />
          </div>
          <div className="grid grid-cols-6 gap-2 w-full h-full">
            <Sidebar />
            <div className="space-y-4 py-4 px-10 col-span-5 overflow-y-auto max-h-[calc(100vh-4rem)]">
              {children}
              <div className="h-4"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
