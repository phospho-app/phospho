"use client";

import { cn } from "@/lib/utils";
import { useUser } from "@propelauth/nextjs/client";
import getConfig from "next/config";
import Link from "next/link";
import { usePostHog } from "posthog-js/react";

import { Separator } from "../ui/separator";
import { NavBarHelp } from "./help";
import { NavBarSettings } from "./navsettings";
import { NavBarProject } from "./project";

let version: string;
try {
  const { serverRuntimeConfig, publicRuntimeConfig } = getConfig();
  version = publicRuntimeConfig.version;
} catch {
  console.log("version not found");
  console.log(getConfig());
}

export function Navbar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const posthog = usePostHog();
  const { user } = useUser();

  return (
    <div>
      <nav className={cn("flex flex-row justify-center", className)} {...props}>
        <div className="flex flex-row items-center justify-between space-y-1 py-1.5 sm:space-y-0 w-10/12">
          <div className="flex flex-row items-baseline align-items">
            <Link href="/">
              <h2 className="text-xl font-semibold text-green-500 flex-none">
                phospho
              </h2>
            </Link>
          </div>
          <div className="flex space-x-2 sm:justify-end items-center">
            {/* <Link
                href="https://forms.gle/KP3oPc9KaHvDsyuE6"
                className="text-sm font-medium text-muted-foreground hover:text-primary mr-4"
                target="_blank"
                onClick={() => {
                  analytics ? logEvent(analytics, "navbar_hub") : null;
                }}
              >
                Hub
              </Link> */}
            {/* <Link
                href="https://blog.phospho.app"
                className="text-sm font-medium text-muted-foreground hover:text-primary mr-4"
                target="_blank"
                onClick={() => {
                  analytics ? logEvent(analytics, "navbar_blog") : null;
                }}
              >
                Blog
              </Link> */}
            {/* <div className="hidden md:flex items-center align-items "></div> */}
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
