"use client";

import { NavBarHelp } from "@/components/navbar/help";
import { NavBarSettings } from "@/components/navbar/navsettings";
import { NavBarProject } from "@/components/navbar/project";
import ShareButton from "@/components/share-button";
import { Sidebar } from "@/components/sidebar/sidebar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { Menu } from "lucide-react";
import Link from "next/link";
import React from "react";

export function Navbar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const [open, setOpen] = React.useState(false);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

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

            <ShareButton selectedOrgId={selectedOrgId} />
          </div>
        </div>
      </nav>
      <Separator />
      {/* <AlphaNotificationBar></AlphaNotificationBar> */}
    </div>
  );
}

export default Navbar;
