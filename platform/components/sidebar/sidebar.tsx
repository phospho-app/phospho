"use client";

import { Button } from "@/components/ui/button";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useRedirectFunctions } from "@propelauth/nextjs/client";
import {
  AreaChart,
  BarChartBig,
  BookOpenText,
  Boxes,
  BriefcaseBusiness,
  CircleUser,
  KeyRound,
  LayoutDashboard,
  LayoutGrid,
  List,
  MessagesSquare,
  Settings,
  Shuffle,
  TextSearch,
  TriangleAlert,
  Users,
  WalletMinimal,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Card, CardContent, CardTitle } from "../ui/card";
import UpgradeButton from "../upgrade-button";
import { OnboardingProgress } from "./sidebar-progress";

interface SideBarElementProps {
  children: React.ReactNode;
  href?: string;
  icon?: any;
  collapsible?: boolean;
  onClick?: () => void;
}

const SideBarElement: React.FC<SideBarElementProps> = ({
  children,
  href,
  icon,
  collapsible = false,
  onClick,
}) => {
  const pathname = usePathname();

  return (
    <>
      {onClick && (
        <Button
          variant={"ghost"}
          className="w-full justify-start h-min py-1"
          onClick={onClick}
        >
          {icon}
          {children}
        </Button>
      )}
      {href && (!pathname.startsWith(href) || collapsible) && (
        <Link href={href}>
          <Button variant={"ghost"} className="w-full justify-start h-min py-1">
            {icon}
            {children}
          </Button>
        </Link>
      )}
      {href && pathname.startsWith(href) && !collapsible && (
        <div className="flex justify-start items-center bg-secondary rounded-md text-sm font-medium h-min px-4 py-1">
          {icon} {children}
        </div>
      )}
    </>
  );
};

function WhiteSpaceSeparator() {
  return <div className="h-4" />;
}

export function Sidebar() {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const pathname = usePathname();
  const [isMobile, setIsMobile] = useState(false);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { redirectToOrgApiKeysPage } = useRedirectFunctions();

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
    <div className="flex flex-col py-4 overflow-y-auto border-secondary h-full ">
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
            <SideBarElement href="/org/transcripts/sessions">
              <List className="h-4 w-4 mr-2" />
              Sessions
            </SideBarElement>
            <SideBarElement href="/org/transcripts/tasks">
              <MessagesSquare className="h-4 w-4 mr-2" />
              Messages
            </SideBarElement>
            <SideBarElement href="/org/transcripts/users">
              <Users className="h-4 w-4 mr-2" />
              Users
            </SideBarElement>
          </div>
        )}
        <SideBarElement
          href="/org/dataviz/"
          icon={<BarChartBig className="h-4 w-4 mr-2" />}
          collapsible={true}
        >
          Dataviz
        </SideBarElement>
        {(pathname.startsWith("/org/dataviz") || isMobile) && (
          <div className="ml-6 text-muted-foreground">
            <SideBarElement href="/org/dataviz/dashboard">
              <LayoutDashboard className="h-4 w-4 mr-2" />
              Dashboard
            </SideBarElement>
            <SideBarElement
              href="/org/dataviz/studio"
              icon={<AreaChart size={16} className="mr-2" />}
            >
              Studio
            </SideBarElement>
          </div>
        )}
        <WhiteSpaceSeparator />
        <SideBarElement
          href="/org/insights/events"
          icon={<TextSearch size={16} className="mr-2" />}
        >
          Analytics
        </SideBarElement>
        <SideBarElement
          href="/org/insights/clusters"
          icon={<Boxes size={16} className="mr-2" />}
        >
          Clusters
        </SideBarElement>
        <SideBarElement
          href="/org/ab-testing"
          icon={<Shuffle size={16} className="mr-2" />}
        >
          AB Testing
        </SideBarElement>
        {/* <SideBarElement
          href="/org/tests"
          icon={<TestTubeDiagonal size={16} className="mr-2" />}
        >
          Tests
        </SideBarElement> */}
        <WhiteSpaceSeparator />
        {/* <WhiteSpaceSeparator /> */}
        <SideBarElement
          href="/org/integrations"
          icon={<LayoutGrid size={16} className="mr-2" />}
        >
          Integrations
        </SideBarElement>
        <SideBarElement
          href="/org/settings"
          icon={<Settings size={16} className="mr-2" />}
          collapsible={true}
        >
          Settings
        </SideBarElement>
        {(pathname.startsWith("/org/settings") || isMobile) && (
          <div className="ml-6 text-muted-foreground">
            <SideBarElement href="/org/settings/project">
              <BriefcaseBusiness size={16} className="mr-2" />
              Project
            </SideBarElement>
            <SideBarElement
              icon={
                <KeyRound size={16} className="scale-x-[-1] rotate-90 mr-2" />
              }
              onClick={() => {
                redirectToOrgApiKeysPage(selectedOrgId ?? "", {
                  redirectBackToUrl: window.location.hostname,
                });
              }}
            >
              API Keys
            </SideBarElement>
            <SideBarElement href="/org/settings/account">
              <CircleUser size={16} className="mr-2" />
              Account
            </SideBarElement>
            <SideBarElement href="/org/settings/billing">
              <WalletMinimal size={16} className="mr-2" />
              Billing
            </SideBarElement>
          </div>
        )}
      </div>

      {selectedOrgMetadata && selectedOrgMetadata?.plan === "hobby" && (
        <div className="flex justify-center mt-4 mx-0.5">
          <Card className="border-red-500 ml-4">
            <CardTitle className="text-sm flex flex-row font-bold p-1">
              <TriangleAlert className="h-6 w-6 mr-2" />
              <h2>Your account is missing billing information</h2>
            </CardTitle>
            <CardContent className="flex flex-col justify-center px-2">
              <p className="mb-2 text-xs text-muted-foreground">
                Advanced analytics are <b>not</b> enabled.
              </p>
              <p className="mb-2 text-xs text-muted-foreground">
                Add payment now to get 10$ of free credits 🎁
              </p>
              <div className="flex justify-center">
                <UpgradeButton
                  tagline="Enable analytics"
                  enlarge={false}
                  green={true}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="absolute bottom-5">
        <OnboardingProgress />
      </div>
    </div>
  );
}
