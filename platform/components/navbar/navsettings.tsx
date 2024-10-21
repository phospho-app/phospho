"use client";

import { SendDataAlertDialog } from "@/components/callouts/import-data";
import { ExportDataButton } from "@/components/navbar/download-csv";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useLogoutFunction, useUser } from "@propelauth/nextjs/client";
import {
  BriefcaseBusiness,
  CircleUser,
  FileUp,
  Moon,
  Settings,
  Star,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useRouter } from "next/navigation";
import * as React from "react";
import useSWR from "swr";

export function NavBarSettings() {
  const { setTheme } = useTheme();
  const { user, accessToken } = useUser();
  const router = useRouter();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const logoutFn = useLogoutFunction();
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const [open, setOpen] = React.useState(false);
  const [dropdownOpen, setDropdownOpen] = React.useState(false);

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  return (
    <div className="flex items-center space-x-2">
      <AlertDialog open={open}>
        <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
          <DropdownMenuTrigger asChild>
            <div>
              <HoverCard openDelay={0} closeDelay={0}>
                <HoverCardTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary h-8 w-8"
                  >
                    <Settings />
                  </Button>
                </HoverCardTrigger>
                <HoverCardContent
                  className="m-0 text-xs text-background bg-foreground"
                  align="center"
                  avoidCollisions={false}
                >
                  <span>Settings</span>
                </HoverCardContent>
              </HoverCard>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel className="space-y-1">
              <div
                onClick={() => {
                  router.push("/org/settings/account");
                  setDropdownOpen(false);
                }}
                className="cursor-pointer hover:text-green-500 flex flex-row items-center"
              >
                <CircleUser className="mr-1 h-5 w-5" />
                {user?.email}
              </div>
              <div
                onClick={() => {
                  router.push("/org/settings/billing");
                  setDropdownOpen(false);
                }}
                className="cursor-pointer ml-2"
              >
                {selectedOrgMetadata &&
                  selectedOrgMetadata?.plan === "hobby" && (
                    <div className="flex items-center text-xs text-muted-foreground hover:text-green-500 font-normal">
                      Hobby user
                    </div>
                  )}
                {selectedOrgMetadata && selectedOrgMetadata?.plan === "pro" && (
                  <div className="flex items-center text-xs text-muted-foreground hover:text-green-500 font-normal">
                    <Star className="mr-1 h-3 w-3" />
                    Pro plan member
                  </div>
                )}
                {selectedOrgMetadata &&
                  selectedOrgMetadata?.plan === "usage_based" && (
                    <div className="flex items-center text-xs text-muted-foreground hover:text-green-500 font-normal">
                      <Star className="mr-1 h-3 w-3" />
                      Usage based billing
                    </div>
                  )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => router.push("/org/settings/project")}
            >
              <div className="flex flex-row items-center">
                <BriefcaseBusiness className="w-4 h-4 mr-1" />
                Project settings
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => {
                setOpen(true);
              }}
            >
              <div className="flex flex-row items-center">
                <FileUp className="w-4 h-4 mr-1" />
                Import data
              </div>
            </DropdownMenuItem>
            <ExportDataButton />
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Sun className="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                <span className="ml-1">Theme</span>
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  Light
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  Dark
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  System
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={async () => {
                // Reset the navigation store
                await logoutFn().then(() => {
                  setSelectedOrgId(null);
                  setproject_id(null);
                  navigationStateStore.persist.clearStorage();
                  router.push("/authenticate");
                });
              }}
            >
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <SendDataAlertDialog setOpen={setOpen} />
      </AlertDialog>
    </div>
  );
}
