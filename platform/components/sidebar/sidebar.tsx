"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import UpgradeButton from "@/components/upgrade-button";
import { authFetcher } from "@/lib/fetcher";
import { cn } from "@/lib/utils";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useRedirectFunctions, useUser } from "@propelauth/nextjs/client";
import {
  AreaChart,
  BarChartBig,
  BookOpenText,
  Boxes,
  BriefcaseBusiness,
  ChevronDown,
  ChevronUp,
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
import { ReactNode, useEffect, useMemo, useState } from "react";
import useSWR from "swr";

import { OnboardingProgress } from "./sidebar-progress";

export interface SidebarState {
  transcriptOpen: boolean;
  datavizOpen: boolean;
  settingsOpen: boolean;
}

interface SideBarElementProps {
  children: React.ReactNode;
  href?: string;
  icon?: ReactNode;
  collapsible?: boolean;
  collapsibleState?: boolean;
  setCollapsibleState?: (state: boolean) => void;
  onClick?: () => void;
}

const SideBarElement: React.FC<SideBarElementProps> = ({
  children,
  href,
  icon,
  collapsible = false,
  collapsibleState,
  setCollapsibleState,
  onClick,
}) => {
  const pathname = usePathname();

  if (!href) {
    return (
      <Button
        variant={"ghost"}
        className="w-full justify-start h-min py-1"
        onClick={onClick}
      >
        {icon}
        {children}
      </Button>
    );
  }

  if (collapsible) {
    return (
      <Button
        variant={"ghost"}
        className="w-full justify-between h-min py-1"
        onClick={() => setCollapsibleState?.(!collapsibleState)}
      >
        <div className="flex flex-grow justify-between items-center">
          <div className="flex h-min items-center">
            {icon}
            {children}
          </div>
          <div>
            {collapsibleState && <ChevronUp className="w-4 h-4" />}
            {!collapsibleState && <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </Button>
    );
  }

  if (href && pathname.startsWith(href)) {
    return (
      <div className="flex justify-start items-center bg-secondary rounded-md text-sm font-medium h-min px-4 py-1">
        {icon} {children}
      </div>
    );
  }

  if (href) {
    return (
      <Link href={href}>
        <Button variant={"ghost"} className="w-full justify-start h-min py-1">
          {icon}
          {children}
        </Button>
      </Link>
    );
  }
};

function WhiteSpaceSeparator() {
  return <div className="h-4" />;
}

export function Sidebar({ className }: { className?: string }) {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const pathname = usePathname();
  const [isMobile, setIsMobile] = useState(false);
  const { redirectToOrgApiKeysPage } = useRedirectFunctions();
  const { accessToken } = useUser();

  const sidebarState = navigationStateStore((state) => state.sidebarState);
  const setSidebarState = navigationStateStore(
    (state) => state.setSidebarState,
  );

  const [hasUpdated, setHasUpdated] = useState(false);
  const sideBarString = useMemo(
    () => JSON.stringify(sidebarState),
    [sidebarState],
  );

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  useEffect(() => {
    // Based on the current pathname, force open the corresponding sidebar elements

    if (sidebarState === null) {
      return;
    }

    // This force open can only happen once.
    // After that, the user can manually close the sidebar elements
    if (hasUpdated) {
      return;
    }

    let updatedState = { ...sidebarState };
    if (pathname.includes("transcripts")) {
      updatedState = { ...updatedState, transcriptOpen: true };
    }
    if (pathname.includes("dataviz")) {
      updatedState = { ...updatedState, datavizOpen: true };
    }
    if (pathname.includes("settings")) {
      updatedState = { ...updatedState, settingsOpen: true };
    }
    setSidebarState(updatedState);
    setHasUpdated(true);
  }, [sideBarString, hasUpdated, pathname, setSidebarState, sidebarState]);

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

  const displayedSidebarState = sidebarState ?? {
    transcriptOpen: true,
    datavizOpen: true,
    settingsOpen: pathname.includes("settings"),
  };

  return (
    <div
      className={cn(
        "overflow-y-auto max-h-[100dvh] md:max-h-full md:h-full",
        className,
      )}
    >
      <div className="flex flex-col py-4 border-secondary h-full">
        <div>
          <SideBarElement
            href="/org/transcripts/"
            icon={<BookOpenText size={16} className="mr-2" />}
            collapsible={true}
            collapsibleState={displayedSidebarState.transcriptOpen}
            setCollapsibleState={(state) =>
              setSidebarState({
                ...displayedSidebarState,
                transcriptOpen: state,
              })
            }
          >
            Transcripts
          </SideBarElement>
          {(displayedSidebarState.transcriptOpen || isMobile) && (
            <div className="ml-6 text-muted-foreground">
              <SideBarElement href="/org/transcripts/sessions">
                <List className="size-4 mr-2" />
                Sessions
              </SideBarElement>
              <SideBarElement href="/org/transcripts/tasks">
                <MessagesSquare className="size-4 mr-2" />
                Messages
              </SideBarElement>
              <SideBarElement href="/org/transcripts/users">
                <Users className="size-4 mr-2" />
                Users
              </SideBarElement>
            </div>
          )}
          <SideBarElement
            href="/org/insights/clusters"
            icon={<Boxes size={16} className="mr-2" />}
          >
            Clusterings
          </SideBarElement>
          <WhiteSpaceSeparator />
          <SideBarElement
            href="/org/insights/events"
            icon={<TextSearch size={16} className="mr-2" />}
          >
            Analytics
          </SideBarElement>
          <SideBarElement
            href="/org/ab-testing"
            icon={<Shuffle size={16} className="mr-2" />}
          >
            AB Testing
          </SideBarElement>
          <SideBarElement
            href="/org/dataviz/"
            icon={<BarChartBig className="size-4 mr-2" />}
            collapsible={true}
            collapsibleState={displayedSidebarState.datavizOpen}
            setCollapsibleState={(state) =>
              setSidebarState({ ...displayedSidebarState, datavizOpen: state })
            }
          >
            Dataviz
          </SideBarElement>
          {(displayedSidebarState.datavizOpen || isMobile) && (
            <div className="ml-6 text-muted-foreground">
              <SideBarElement href="/org/dataviz/dashboard">
                <LayoutDashboard className="size-4 mr-2" />
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
            collapsibleState={displayedSidebarState.settingsOpen}
            setCollapsibleState={(state) =>
              setSidebarState({ ...displayedSidebarState, settingsOpen: state })
            }
          >
            Settings
          </SideBarElement>
          {(displayedSidebarState.settingsOpen || isMobile) && (
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

        <div className="md:flex-grow" />
        <OnboardingProgress />
        <div className="h-10" />
      </div>
    </div>
  );
}
