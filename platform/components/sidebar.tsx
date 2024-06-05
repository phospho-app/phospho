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
import { useState } from "react";

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

  if (!collapsible) {
    return (
      <Link href={href}>
        <Button
          variant={pathname.startsWith(href) ? "secondary" : "ghost"}
          className="w-full justify-start"
        >
          {icon}
          {children}
        </Button>
      </Link>
    );
  }

  if (collapsible) {
    return (
      <Link href={href}>
        <Button variant="ghost" className="w-full justify-between">
          <div className="flex justify-start items-center">
            {icon}
            {children}
          </div>
          <Button variant="ghost" size="icon" asChild></Button>
        </Button>
      </Link>
    );
  }
}

export function Sidebar() {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const pathname = usePathname();

  return (
    <>
      <div className="relative flex-grow max-h-[calc(100vh-6rem)] flex flex-col border-r py-4 overflow-y-auto border-secondary">
        <div>
          <SideBarElement
            href="/org/transcripts/"
            icon={<BookOpenText size={16} className="mr-2" />}
            collapsible={true}
          >
            Transcripts
          </SideBarElement>
          {pathname.startsWith("/org/transcripts") && (
            <div className="ml-6 text-muted-foreground">
              <SideBarElement href="/org/transcripts/tasks">
                Tasks
              </SideBarElement>
              <SideBarElement href="/org/transcripts/sessions">
                Sessions
              </SideBarElement>
              <SideBarElement href="/org/transcripts/users">
                Users
              </SideBarElement>
              <SideBarElement href="/org/transcripts/dashboard">
                Dashboard
              </SideBarElement>
            </div>
          )}
          <Separator />
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
          <Separator />
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
          <Separator />
          <SideBarElement
            href="/org/settings"
            icon={<Settings size={16} className="mr-2" />}
          >
            Settings
          </SideBarElement>
        </div>

        <div className="flex justify-center mx-2 mb-4 mt-4">
          {selectedOrgMetadata && selectedOrgMetadata?.plan === "hobby" && (
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
          )}
        </div>
      </div>
    </>
  );
}
