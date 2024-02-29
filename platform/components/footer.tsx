import {
  DiscordLogoIcon,
  GitHubLogoIcon,
  LinkedInLogoIcon,
  TwitterLogoIcon,
} from "@radix-ui/react-icons";
import Link from "next/link";

export default function FooterDemo() {
  return (
    <footer>
      <div className=" relative bottom-0 inset-x-0 w-full}">
        <div className="container flex flex-col flex-wrap items-center items-align justify-center mx-auto  lg:justify-between">
          <div className="flex justify-center space-x-2 mt-4 lg:mt-0">
            <Link href={"https://github.com/phospho-app"}>
              <GitHubLogoIcon />
            </Link>
            <Link href={"https://twitter.com/phospho_app"}>
              <TwitterLogoIcon />
            </Link>
            <Link href={"https://discord.gg/Pu4Hf9UAJC"}>
              <DiscordLogoIcon />
            </Link>
            <Link href={"https://www.linkedin.com/company/phospho-app"}>
              <LinkedInLogoIcon />
            </Link>
          </div>
        </div>
        <div>
          <div className="flex justify-center space-x-2 mt-4 py-2 lg:mt-0">
            <p className="text-center text-muted-foreground">
              Phospho @2023 - All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
