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
import {
  Calendar,
  CandlestickChart,
  Flag,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
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
  let lastEvalSourceFilter: string | null = null;

  for (const [key, value] of Object.entries(tasksColumnsFilters)) {
    if (key === "flag" && (typeof value === "string" || value === null)) {
      flagFilter = value;
    }
    if (key === "event" && typeof value === "string") {
      eventFilter = eventFilter == null ? [value] : eventFilter.concat(value);
    }
    if (key === "lastEvalSource" && typeof value === "string") {
      lastEvalSourceFilter = value;
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
            <Button variant="outline">Select filters</Button>
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
              {flagFilter}
              <X className="h-4 w-4 ml-2" />
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
              {eventFilter.join(", ")}
              <X className="h-4 w-4 ml-2" />
            </Button>
          )}
          {lastEvalSourceFilter !== null && (
            <Button
              className="ml-2"
              variant="outline"
              onClick={() => {
                setTasksColumnsFilters((prevFilters) => ({
                  ...prevFilters,
                  lastEvalSource: null,
                }));
              }}
            >
              {lastEvalSourceFilter}
              <X className="h-4 w-4 ml-2" />
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
              <Calendar className="h-4 w-4 mr-2" />
              <span>Events</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent className="overflow-y-auto">
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
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <CandlestickChart className="h-4 w-4 mr-2" />
              <span>Last Eval Source</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem
                  onClick={() => {
                    setTasksColumnsFilters((prevFilters) => ({
                      ...prevFilters,
                      lastEvalSource: "phospho",
                    }));
                  }}
                  style={{
                    color:
                      lastEvalSourceFilter === "phospho" ? "green" : "inherit",
                  }}
                >
                  phospho
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setTasksColumnsFilters((prevFilters) => ({
                      ...prevFilters,
                      lastEvalSource: "user",
                    }));
                  }}
                  style={{
                    color:
                      lastEvalSourceFilter === "user" ? "green" : "inherit",
                  }}
                >
                  user
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default FilterComponent;
