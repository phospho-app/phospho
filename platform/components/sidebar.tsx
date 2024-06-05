"use client";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { dataStateStore } from "@/store/store";
import {
  BarChartBig,
  BookOpenText,
  Boxes,
  ChevronDown,
  ChevronUp,
  ListChecks,
  Monitor,
  Settings,
  Shuffle,
  Sparkles,
  Star,
  TestTubeDiagonal,
  TextSearch,
  User2,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader } from "./ui/card";
import UpgradeButton from "./upgrade-button";

function SideBarElement({
  href,
  icon,
  children,
  collapsible = false,
}: {
  href: string;
  icon?: any;
  children?: React.ReactNode;
  collapsible?: boolean;
}) {
  const pathname = usePathname();

  return (
    <>
      {(!pathname.startsWith(href) || collapsible) && (
        <Link href={href}>
          <Button variant={"ghost"} className="w-full justify-start h-min py-1">
            {icon}
            {children}
          </Button>
        </Link>
      )}
      {pathname.startsWith(href) && !collapsible && (
        <div className="flex justify-start items-center bg-secondary rounded-md text-sm font-medium h-min px-4 py-1">
          {icon} {children}
        </div>
      )}
    </>
  );
}

function WhiteSpaceSeparator() {
  return <div className="h-4" />;
}

export function Sidebar() {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const pathname = usePathname();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      // Update the state based on the window width
      setIsMobile(window.innerWidth < 768); // Adjust the threshold according to your design
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

  return (
    <div className="flex flex-col py-4 overflow-y-auto border-secondary h-full">
      <div>
        <SideBarElement
          href="/org/transcripts/"
          icon={<BookOpenText size={16} className="mr-2" />}
          collapsible={true}
        >
          Transcripts
        </SideBarElement>
        {(pathname.startsWith("/org/transcripts") || isMobile) && (
          <div className="ml-6 text-muted-foreground">
            <SideBarElement href="/org/transcripts/tasks">Tasks</SideBarElement>
            <SideBarElement href="/org/transcripts/sessions">
              Sessions
            </SideBarElement>
            <SideBarElement href="/org/transcripts/users">Users</SideBarElement>
            <SideBarElement href="/org/transcripts/dashboard">
              Dashboard
            </SideBarElement>
          </div>
        )}
        <WhiteSpaceSeparator />
        <SideBarElement
          href="/org/insights/clusters"
          icon={<Boxes size={16} className="mr-2" />}
        >
          Clusters
        </SideBarElement>
        <SideBarElement
          href="/org/insights/events"
          icon={<TextSearch size={16} className="mr-2" />}
        >
          Events
        </SideBarElement>
        <SideBarElement
          href="/org/insights/dataviz"
          icon={<BarChartBig size={16} className="mr-2" />}
        >
          Dataviz
        </SideBarElement>
        <WhiteSpaceSeparator />
        <SideBarElement
          href="/org/ab-testing"
          icon={<Shuffle size={16} className="mr-2" />}
        >
          AB Testing
        </SideBarElement>
        <SideBarElement
          href="/org/tests"
          icon={<TestTubeDiagonal size={16} className="mr-2" />}
        >
          Tests
        </SideBarElement>
        <WhiteSpaceSeparator />
        <SideBarElement
          href="/org/settings"
          icon={<Settings size={16} className="mr-2" />}
        >
          Settings
        </SideBarElement>
      </div>

      {selectedOrgMetadata && selectedOrgMetadata?.plan === "hobby" && (
        <div className="flex justify-center mx-2 mb-4 mt-4">
          <Card>
            <CardContent className="flex justify-center mb-0">
              <div>
                <div className="flex items-baseline">
                  <Sparkles className="h-4 w-4 text-green-500 mr-1" />
                  <h2 className="font-semibold mt-4 mb-1">Complete setup</h2>
                </div>
                <p className="mb-2 text-sm">
                  Enable automatic evaluation and event detection
                </p>
                <div className="flex justify-center">
                  <UpgradeButton
                    tagline="Add payment method"
                    enlarge={false}
                    green={false}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
