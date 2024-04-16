import { Button } from "@/components/ui/button";
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
} from "@/components/ui/dropdown-menu";
import { useUser } from "@propelauth/nextjs/client";
import { DiscordLogoIcon } from "@radix-ui/react-icons";
import { Dot, HelpCircle, LifeBuoy, MailIcon } from "lucide-react";
import Link from "next/link";
import { usePostHog } from "posthog-js/react";
import React from "react";

import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "../ui/hover-card";

export function NavBarHelp() {
  const { user } = useUser();
  const posthog = usePostHog();

  const [hasClicked, setHasClicked] = React.useState(false);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div>
          <HoverCard openDelay={50} closeDelay={50}>
            <HoverCardTrigger>
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-primary"
                // onClick={() => {
                //   setHasClicked(true);
                // }}
              >
                {/* // Add a red dot on the top right of the help icon */}
                <div className="relative h-6 w-6">
                  <Dot className="absolute text-red-500 z-10 -top-4 -right-4 w-10 h-10" />
                  <HelpCircle className="z-0 w-6 h-6" />
                </div>
              </Button>
            </HoverCardTrigger>
            <HoverCardContent
              className="m-0 text-xs text-background bg-foreground"
              align="center"
            >
              <span>Help</span>
            </HoverCardContent>
          </HoverCard>
        </div>
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
              <LifeBuoy className="w-6 h-6 mr-2" />
              <span> Documentation</span>
            </div>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>Get started</DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuItem>
              <Link
                href="https://docs.phospho.ai/getting-started"
                target="_blank"
              >
                Quickstart
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Link
                href="https://colab.research.google.com/drive/1Wv9KHffpfHlQCxK1VGvP_ofnMiOGK83Q"
                target="_blank"
              >
                Example Colab notebook
              </Link>
            </DropdownMenuItem>
          </DropdownMenuSubContent>
        </DropdownMenuSub>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <Link href="https://discord.gg/MXqBJ9pBsx" target="_blank">
            <div className="flex items-center">
              <DiscordLogoIcon className="w-6 h-6 mr-2" />
              Join Discord
            </div>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>
            <div className="flex items-center">
              <MailIcon className="w-6 h-6 mr-2" />
              Contact us
            </div>
          </DropdownMenuSubTrigger>
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
