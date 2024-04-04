"use client";

import { cn } from "@/lib/utils";
import { useUser } from "@propelauth/nextjs/client";
import { TrafficCone } from "lucide-react";
import getConfig from "next/config";
import Link from "next/link";
import { usePostHog } from "posthog-js/react";

import LogoutButton from "./logout-button";
import { ModeToggle } from "./togglemode";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";

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
  // PostHog
  const posthog = usePostHog();
  // PropelAuth
  const { user, loading, accessToken } = useUser();

  return (
    <div>
      <nav
        className={cn("flex items-center space-x-4 lg:space-x-6", className)}
        {...props}
      >
        <div className="container flex flex-row items-center justify-between space-y-1 py-2 sm:space-y-0">
          <div className="flex flex-row items-baseline align-items">
            <Link href="/">
              <h2 className="text-lg font-semibold text-green-500 flex-none">
                phospho
              </h2>
            </Link>
            <span className="text-sm mr-4 text-gray-300 pl-4 w-32">
              {/* {version} */}
              <TrafficCone className="h-6 w-6 inline pr-1" />
              Beta version
            </span>
            <Link
              href="https://a6gysudbx4d.typeform.com/to/V4dZO5A3"
              target="_blank"
            >
              <Button
                className="text-muted-foreground hover:text-primary"
                variant="ghost"
                onClick={() => {
                  posthog.capture("navbar_contact", {
                    propelauthUserId: user?.userId,
                    userEmail: user?.email,
                  });
                }}
              >
                Give feedback
              </Button>
            </Link>
          </div>
          <div className="ml-auto flex space-x-2 sm:justify-end">
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
            <div className="hidden md:flex items-center align-items "></div>

            <Link href="https://docs.phospho.ai" target="_blank">
              <Button
                className="text-muted-foreground hover:text-primary"
                variant="ghost"
                onClick={() =>
                  posthog.capture("navbar_to_docs", {
                    propelauthUserId: user?.userId,
                    userEmail: user?.email,
                  })
                }
              >
                Documentation
              </Button>
            </Link>
            <LogoutButton />
            <Link href="https://cal.com/nicolas-oulianov" target="_blank">
              <Button
                className=" bg-green-600 text-white hover:bg-green-500 hover:text-white"
                variant="outline"
                onClick={() =>
                  posthog.capture("navbar_need_help", {
                    propelauthUserId: user?.userId,
                    userEmail: user?.email,
                  })
                }
              >
                Book free call
              </Button>
            </Link>
            <ModeToggle />
          </div>
        </div>
      </nav>
      <Separator />
      {/* <AlphaNotificationBar></AlphaNotificationBar> */}
    </div>
  );
}

export default Navbar;
