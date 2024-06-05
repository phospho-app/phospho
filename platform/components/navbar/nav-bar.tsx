"use client";

import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { Menu } from "lucide-react";
import getConfig from "next/config";
import Link from "next/link";
import React from "react";

import { Separator } from "../ui/separator";
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

  return (
    <div>
      <nav className={cn("flex flex-row justify-center", className)} {...props}>
        <div className="flex flex-row items-center justify-between py-1.5 md:w-10/12">
          <div className="flex flex-row items-center space-x-2">
            <div className="block md:hidden">
              <DropdownMenu open={open} onOpenChange={setOpen}>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Menu className="h-6 w-6 text-muted-foreground" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    setOpen(false);
                  }}
                >
                  <Sidebar />
                </DropdownMenuContent>
              </DropdownMenu>
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
          </div>
        </div>
      </nav>
      <Separator />
      {/* <AlphaNotificationBar></AlphaNotificationBar> */}
    </div>
  );
}

export default Navbar;
