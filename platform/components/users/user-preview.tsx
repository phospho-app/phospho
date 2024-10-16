import { DatePickerWithRange } from "@/components/date-range";
import { SessionsTable } from "@/components/sessions/sessions-table";
import { TasksTable } from "@/components/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

function UserPreview({ user_id }: { user_id?: string }) {
  const [selected, setSelected] = useState<string>("Messages");

  if (!user_id) return <></>;

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex flex-row justify-between items-end mt-4">
        <div className="text-xl font-bold">User {user_id}</div>
        <Link href={`/org/transcripts/users/${encodeURIComponent(user_id)}`}>
          <Button>
            Go to User <ChevronRight />
          </Button>
        </Link>
      </div>
      <div className="flex flex-row gap-x-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild className="w-[10rem] justify-between">
            <Button variant="secondary">
              {selected}
              <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={() => setSelected("Messages")}>
              Messages
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => setSelected("Sessions")}>
              Sessions
            </DropdownMenuItem>
          </DropdownMenuContent>
          <DropdownMenu />
        </DropdownMenu>
        <DatePickerWithRange />
      </div>
      {selected === "Messages" && (
        <TasksTable forcedDataFilters={{ user_id: user_id }} />
      )}
      {selected === "Sessions" && (
        <SessionsTable forcedDataFilters={{ user_id: user_id }} />
      )}
    </div>
  );
}

export { UserPreview };
