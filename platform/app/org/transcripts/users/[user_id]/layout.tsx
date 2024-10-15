"use client";

import { DatePickerWithRange } from "@/components/date-range";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { navigationStateStore } from "@/store/store";
import { ChevronDown, ChevronLeft } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

function capitalizeFirstLetter(string?: string) {
  if (!string) return string;
  return string.charAt(0).toUpperCase() + string.slice(1);
}

export default function Page({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { user_id: string };
}) {
  const router = useRouter();
  const user_id = decodeURIComponent(params.user_id);
  const pathname = usePathname();
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );

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

  useEffect(() => {
    setDateRangePreset("all-time");
  }, [setDateRangePreset]);

  return (
    <div className="flex flex-col gap-y-2">
      <div>
        <Button
          onClick={() => router.push("/org/transcripts/users")}
          className="max-w-[10rem]"
        >
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Users
        </Button>
      </div>
      <div className="text-2xl font-bold tracking-tight">User {user_id}</div>
      <div className="flex flex-row gap-x-2">
        <DatePickerWithRange />
        <DropdownMenu>
          <DropdownMenuTrigger asChild className="w-[10rem] justify-between">
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
    </div>
  );
}
