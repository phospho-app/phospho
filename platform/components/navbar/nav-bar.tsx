"use client";

import { Sidebar } from "@/components/sidebar/sidebar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { useRedirectFunctions, useUser } from "@propelauth/nextjs/client";
import { Menu, Share2 } from "lucide-react";
import getConfig from "next/config";
import Link from "next/link";
import React from "react";

import { NavBarHelp } from "./help";
import { NavBarSettings } from "./navsettings";
import { NavBarProject } from "./project";

let version: string;
try {
  const { publicRuntimeConfig } = getConfig();
  version = publicRuntimeConfig.version;
} catch {
  console.log("version not found");
  console.log(getConfig());
}

export function Navbar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const [open, setOpen] = React.useState(false);
  const { redirectToOrgPage } = useRedirectFunctions();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { user } = useUser();
  // The share button is only visible if the user has the permission to invite others
  // This button redirects to propelauth user management page
  const userCanInviteOthers =
    selectedOrgId && user?.orgIdToOrgMemberInfo
      ? user.orgIdToOrgMemberInfo[selectedOrgId].hasPermission(
          "propelauth::can_invite",
        )
      : false;

  return (
    <div>
      <nav
        className={cn(
          "relative flex flex-row w-full md:justify-center",
          className,
        )}
        {...props}
      >
        <div className="flex flex-row  w-full items-center justify-between mx-1.5 my-1.5 md:w-10/12">
          <div className="flex flex-row items-center space-x-2 ">
            <div className="block md:hidden">
              <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Menu className="h-6 w-6 text-muted-foreground" />
                  </Button>
                </SheetTrigger>
                <SheetContent
                  side="left"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    setOpen(false);
                  }}
                >
                  <Sidebar />
                </SheetContent>
              </Sheet>
            </div>
            <Link href="/">
              <h2 className="text-xl font-semibold text-green-500 flex-none">
                phospho
              </h2>
            </Link>
          </div>
          <div className="flex space-x-2 sm:justify-end items-center">
            <NavBarHelp />
            <NavBarSettings />
            <NavBarProject />

            {userCanInviteOthers && selectedOrgId && (
              <Button
                className="h-8"
                onClick={() => redirectToOrgPage(selectedOrgId)}
                variant="outline"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
            )}
          </div>
        </div>
      </nav>
      <Separator />
      {/* <AlphaNotificationBar></AlphaNotificationBar> */}
    </div>
  );
}

export default Navbar;
