"use client";

import { SendDataAlertDialog } from "@/components/callouts/import-data";
import DownloadButton from "@/components/navbar/download-csv";
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog";
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
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useLogoutFunction, useUser } from "@propelauth/nextjs/client";
import { FileUp, Moon, Settings, Star, Sun, Upload } from "lucide-react";
import { useTheme } from "next-themes";
import { useRouter } from "next/navigation";
import * as React from "react";

export function NavBarSettings() {
  const { setTheme } = useTheme();
  const { user } = useUser();
  const router = useRouter();
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const hasTasks = dataStateStore((state) => state.hasTasks);

  const logoutFn = useLogoutFunction();
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const [open, setOpen] = React.useState(false);

  return (
    <div className="flex items-center space-x-2">
      <AlertDialog open={open}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <div>
              <HoverCard openDelay={50} closeDelay={50}>
                <HoverCardTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary"
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
            <DropdownMenuLabel>
              <div>{user?.email}</div>
              {selectedOrgMetadata && selectedOrgMetadata?.plan === "hobby" && (
                <div className="flex items-center text-xs text-muted-foreground hover:text-green-500 font-normal">
                  Hobby user
                </div>
              )}
              {selectedOrgMetadata && selectedOrgMetadata?.plan === "pro" && (
                <div className="flex items-center text-xs text-muted-foreground hover:text-green-500 font-normal">
                  <Star className="mr-1 h-4 w-4" />
                  Pro plan member
                </div>
              )}
              {selectedOrgMetadata &&
                selectedOrgMetadata?.plan === "usage_based" && (
                  <div className="flex items-center text-xs text-muted-foreground hover:text-green-500 font-normal">
                    <Star className="mr-1 h-4 w-4" />
                    Usage based billing
                  </div>
                )}
            </DropdownMenuLabel>

            <DropdownMenuItem
              onClick={() => router.push("/org/settings/account")}
            >
              Account settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => router.push("/org/settings/project")}
            >
              Project settings
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => router.push("/org/settings/billing")}
            >
              Billing settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Sun className="h-6 w-6 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-6 w-6 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                <span className="ml-2">Theme</span>
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
            <DropdownMenuItem>
              <AlertDialogTrigger
                onClick={() => {
                  setOpen(true);
                }}
              >
                <div className="flex flex-row items-center">
                  <FileUp className="w-6 h-6 mr-2" />
                  Import data
                </div>
              </AlertDialogTrigger>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <DownloadButton />
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={async () => {
                // Reset the navigation store
                await logoutFn().then(() => {
                  setSelectedOrgId(null);
                  setproject_id(null);
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
