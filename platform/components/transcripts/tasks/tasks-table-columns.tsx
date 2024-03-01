import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Event } from "@/models/events";
import { TaskWithEvents } from "@/models/tasks";
import { dataStateStore } from "@/store/store";
import { ColumnDef, filterFns } from "@tanstack/react-table";
import { ArrowUpDown, ChevronDown, ChevronRight, Sparkles } from "lucide-react";

import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../../ui/dropdown-menu";

export function getColumns({
  handleViewClick,
}: {
  handleViewClick: (task: TaskWithEvents) => void;
}): ColumnDef<TaskWithEvents>[] {
  const uniqueEventNamesInData = dataStateStore(
    (state) => state.uniqueEventNamesInData,
  );

  const columns: ColumnDef<TaskWithEvents>[] = [
    // id
    {
      filterFn: (row, id, filterValue) => {
        // if is in the filtervalue
        if (filterValue === null) return true;
        return filterValue.includes(row.original.id);
      },
      header: "",
      accessorKey: "id",
      cell: ({ row }) => {
        row.original.id;
      },
      enableHiding: true,
    },
    // Date
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Date
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "created_at",
      cell: ({ row }) => (
        <span onClick={() => handleViewClick(row.original)}>
          {formatUnixTimestampToLiteralDatetime(
            Number(row.original.created_at),
          )}
        </span>
      ),
    },
    // Flag
    {
      header: ({ column }) => {
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                onClick={() =>
                  column.toggleSorting(column.getIsSorted() === "asc")
                }
              >
                <Sparkles className="h-4 w-4 mr-1 text-green-500" />
                Eval
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem
                onClick={() => column.setFilterValue("success")}
              >
                Success
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => column.setFilterValue("failure")}
              >
                Failure
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => column.setFilterValue(null)}>
                Clear
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
      accessorKey: "flag",
      cell: (row) => (
        <span>
          <Badge
            variant={
              (row.getValue() as string) === "success"
                ? "secondary"
                : (row.getValue() as string) === "failure"
                  ? "destructive"
                  : "secondary"
            }
          >
            {row.getValue() as string}
          </Badge>
        </span>
      ),
    },
    // Events
    {
      filterFn: (row, id, filterValue) => {
        if (filterValue === null) return true;
        // If the filter value is not null, return whether
        // the filterValue is in [event.event_name] array
        return (row.original.events as Event[]).some(
          (event) => event.event_name === filterValue,
        );
      },
      header: ({ column }) => {
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                onClick={() =>
                  column.toggleSorting(column.getIsSorted() === "asc")
                }
              >
                <Sparkles className="h-4 w-4 mr-1 text-green-500" />
                Events
                <ChevronDown size={16} className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              {uniqueEventNamesInData.map((eventName) => (
                <DropdownMenuItem
                  key={eventName}
                  onClick={() => column.setFilterValue(eventName)}
                >
                  {eventName}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                key="event_clear"
                onClick={() => column.setFilterValue(null)}
              >
                Clear
              </DropdownMenuItem>
            </DropdownMenuContent>
            <DropdownMenu />
          </DropdownMenu>
        );
      },
      accessorKey: "events",
      cell: (row) => (
        <span>
          {(row.getValue() as Event[]).map((event: Event) => (
            <Badge
              key={event.id}
              variant="secondary"
              className="ml-2 mt-1 mb-1"
            >
              {event.event_name as string}
            </Badge>
          ))}
        </span>
      ),
    },
    {
      header: "Input",
      accessorKey: "input",
    },
    {
      header: "Output",
      accessorKey: "output",
      cell: (row) => {
        const output = row.getValue() as string; // asserting the type as string
        return (
          <span>
            {output
              ? output.length > 50
                ? output.substring(0, 50) + "..."
                : output
              : "-"}
          </span>
        );
      },
    },
    {
      header: "View",
      cell: ({ row }) => {
        const task = row.original;
        // Match the task object with this key
        // Handle undefined edge case
        if (!task) return <></>;
        return (
          <Button variant="ghost" onClick={() => handleViewClick(task)}>
            <ChevronRight />
          </Button>
        );
      },
    },
  ];
  return columns;
}
