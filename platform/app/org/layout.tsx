"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import FetchHasTasksSessions from "@/components/fetch-data/fetch-tasks-sessions";
import Navbar from "@/components/nav-bar";
import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { dataStateStore } from "@/store/store";
import { LucideSmartphone } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

export default function OrgLayout({ children }: { children: React.ReactNode }) {
  const [isMobile, setIsMobile] = useState(false);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const router = useRouter();

  if (selectedOrgMetadata?.plan === "hobby") {
    // Uncomment this to enable the paywall
    // router.push("/onboarding/plan");
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
          <div className="grid grid-cols-5 gap-5 w-full h-full">
            <Sidebar />
            <div className="space-y-4 py-4 px-10 col-span-4 overflow-y-auto max-h-[calc(100vh-4rem)]">
              {children}
              <div className="h-4"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
