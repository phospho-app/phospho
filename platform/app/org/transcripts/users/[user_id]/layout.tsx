"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, ChevronLeft } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

function capitalizeFirstLetter(string?: string) {
  if (!string) return string;
  return string.charAt(0).toUpperCase() + string.slice(1);
}

export default function Page({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { id: string };
}) {
  const router = useRouter();
  const user_id = decodeURIComponent(params.id);
  const pathname = usePathname();
  let currentTabName = pathname.split("/").pop();
  if (currentTabName !== "messages" && currentTabName !== "sessions") {
    currentTabName = "messages";
  }
  const [selected, setSelected] = useState<string>(
    capitalizeFirstLetter(currentTabName) ?? "Messages",
  );

  const handleSelect = (event: Event) => {
    const target = event.target as HTMLButtonElement;
    if (!target?.textContent) return;
    setSelected(target.textContent);
    router.push(
      `/org/transcripts/users/${user_id}/${target.textContent.toLowerCase()}`,
    );
  };

  return (
    <>
      <div>
        <Button onClick={() => router.push("/org/transcripts/users")}>
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Users
        </Button>
      </div>
      <div className="flex flex-row space-x-2">
        <div className="text-3xl font-bold tracking-tight mr-8">
          User {user_id}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild className="w-32 justify-between">
            <Button variant="secondary">
              {selected}
              <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={handleSelect}>
              Messages
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={handleSelect}>
              Sessions
            </DropdownMenuItem>
          </DropdownMenuContent>
          <DropdownMenu />
        </DropdownMenu>
      </div>
      {children}
    </>
  );
}
