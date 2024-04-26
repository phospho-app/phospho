import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { navigationStateStore } from "@/store/store";
import { dataStateStore } from "@/store/store";
import { enIE } from "date-fns/locale";
import { Calendar, Flag, ThumbsDown, ThumbsUp } from "lucide-react";
import React from "react";

const FilterComponent = ({}: React.HTMLAttributes<HTMLDivElement>) => {
  const setTasksColumnsFilters = navigationStateStore(
    (state) => state.setTasksColumnsFilters,
  );
  const tasksColumnsFilters = navigationStateStore(
    (state) => state.tasksColumnsFilters,
  );

  let eventFilter: string[] | null = null;
  let flagFilter: string | null = null;
  let metadata: Record<string, any> | null = null;

  for (const [key, value] of Object.entries(tasksColumnsFilters)) {
    if (key === "flag" && (typeof value === "string" || value === null)) {
      flagFilter = value;
    }
    if (key === "event" && typeof value === "string") {
      eventFilter = eventFilter == null ? [value] : eventFilter.concat(value);
    }
    if (key === "metadata" && typeof value === "object") {
      metadata = value;
    }
  }

  const selectedProject = dataStateStore((state) => state.selectedProject);

  if (!selectedProject) {
    return <></>;
  }

  const events = selectedProject.settings?.events;

  return (
    <div>
      <DropdownMenu>
        <div className="flex align-items">
          <DropdownMenuTrigger asChild>
            <Button className="mb-2" variant="outline">
              Select filters
            </Button>
          </DropdownMenuTrigger>
          {flagFilter !== null && (
            <Button
              className={`ml-2 color: ${flagFilter === "success" ? "green" : "red"} `}
              variant="outline"
              onClick={() => {
                setTasksColumnsFilters((prevFilters) => ({
                  ...prevFilters,
                  flag: null,
                }));
              }}
            >
              <Flag className="h-4 w-4 mr-2" />
              {flagFilter}
            </Button>
          )}
          {eventFilter !== null && (
            <Button
              className="ml-2"
              variant="outline"
              onClick={() => {
                setTasksColumnsFilters((prevFilters) => ({
                  ...prevFilters,
                  event: null,
                }));
              }}
            >
              <Calendar className="h-4 w-4 mr-2" />
              {eventFilter.join(", ")}
            </Button>
          )}
        </div>
        <DropdownMenuContent className="w-56">
          <DropdownMenuLabel>Filters to apply</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {/* Flag */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Flag className="h-4 w-4 mr-2" />
              <span>Eval</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem
                  onClick={() => {
                    setTasksColumnsFilters((prevFilters) => ({
                      ...prevFilters,
                      flag: "success",
                    }));
                  }}
                  style={{
                    color: flagFilter === "success" ? "green" : "inherit",
                  }}
                >
                  <ThumbsUp className="h-4 w-4 mr-2" />
                  <span>Success</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setTasksColumnsFilters((prevFilters) => ({
                      ...prevFilters,
                      flag: "failure",
                    }));
                  }}
                  style={{
                    color: flagFilter === "failure" ? "red" : "inherit",
                  }}
                >
                  <ThumbsDown className="h-4 w-4 mr-2" />
                  <span>Failure</span>
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Calendar className="h-4 w-4 mr-2 " />
              <span>Events</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                {events &&
                  Object.entries(events).map(([event_name, event]) => {
                    return (
                      <DropdownMenuItem
                        key={event.id}
                        onClick={() => {
                          setTasksColumnsFilters((prevFilters) => ({
                            ...prevFilters,
                            event: event_name,
                          }));
                        }}
                        style={{
                          color: eventFilter?.includes(event_name)
                            ? "green"
                            : "inherit",
                        }}
                      >
                        {event_name}
                      </DropdownMenuItem>
                    );
                  })}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default FilterComponent;
