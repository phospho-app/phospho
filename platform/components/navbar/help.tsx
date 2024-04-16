import { useUser } from "@propelauth/nextjs/client";
import { Circle, Dot, HelpCircle, LifeBuoy } from "lucide-react";
import Link from "next/link";
import { usePostHog } from "posthog-js/react";
import React from "react";

import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";

export function NavBarHelp() {
  const { user } = useUser();
  const posthog = usePostHog();

  const [hasClicked, setHasClicked] = React.useState(false);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setHasClicked(true)}
          className="text-muted-foreground hover:text-primary"
        >
          <HelpCircle className="z-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem>
          <Link
            href="https://docs.phospho.ai"
            target="_blank"
            onClick={() =>
              posthog.capture("navbar_to_docs", {
                propelauthUserId: user?.userId,
                userEmail: user?.email,
              })
            }
          >
            <div className="flex items-center">
              <LifeBuoy className="w-4 h-4 mr-1" />
              <span> Documentation</span>
            </div>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>Contact us</DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuItem>
              <Link
                href="https://cal.com/nicolas-oulianov"
                target="_blank"
                onClick={() =>
                  posthog.capture("navbar_need_help", {
                    propelauthUserId: user?.userId,
                    userEmail: user?.email,
                  })
                }
              >
                Contact support
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Link
                href="https://cal.com/paul-louis"
                target="_blank"
                onClick={() =>
                  posthog.capture("navbar_contact_sales", {
                    propelauthUserId: user?.userId,
                    userEmail: user?.email,
                  })
                }
              >
                Contact sales
              </Link>
            </DropdownMenuItem>
          </DropdownMenuSubContent>
        </DropdownMenuSub>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <Link
            href="https://a6gysudbx4d.typeform.com/to/V4dZO5A3"
            target="_blank"
            onClick={() => {
              posthog.capture("navbar_contact", {
                propelauthUserId: user?.userId,
                userEmail: user?.email,
              });
            }}
          >
            Give feedback
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
