"use client";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { format } from "date-fns";
import { Calendar as CalendarIcon, ChevronDown, X } from "lucide-react";
import { useEffect, useState } from "react";
import * as React from "react";

import { HoverCard, HoverCardContent, HoverCardTrigger } from "./ui/hover-card";
import { Separator } from "./ui/separator";

export function DatePickerWithRange({
  className,
  nbrItems = undefined,
}: {
  className?: React.HTMLAttributes<HTMLDivElement>;
  nbrItems?: number | null;
}) {
  const dateRangePreset = navigationStateStore(
    (state) => state.dateRangePreset,
  );
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);
  const setDateRange = navigationStateStore((state) => state.setDateRange);
  const warningShown = navigationStateStore((state) => state.warningShowed);
  const setWarningShowed = navigationStateStore(
    (state) => state.setWarningShowed,
  );
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    const showCondition =
      !warningShown && nbrItems === null && dateRangePreset === "last-7-days";
    if (showCondition) {
      setShowWarning(true);
      setWarningShowed(true);
    }
  }, [nbrItems, dateRangePreset, setWarningShowed, warningShown]);

  const closeWarning = () => {
    setShowWarning(false);
  };

  let dateRangeLabel = "";
  if (dateRangePreset === "last-24-hours") {
    dateRangeLabel = "Last 24 hours";
  }
  if (dateRangePreset === "last-7-days") {
    dateRangeLabel = "Last 7 days";
  }
  if (dateRangePreset === "last-30-days") {
    dateRangeLabel = "Last 30 days";
  }
  if (dateRangePreset === "all-time") {
    dateRangeLabel = "All time";
  }
  if (dateRangePreset === null) {
    try {
      if (dateRange?.from && dateRange.to) {
        dateRangeLabel = `${format(dateRange.from, "y-LLL-dd")} - ${format(
          dateRange.to,
          "y-LLL-dd",
        )}`;
      } else if (dateRange?.from && !dateRange.to) {
        dateRangeLabel = `${format(dateRange.from, "y-LLL-dd")}`;
      } else {
        dateRangeLabel = "Pick a date";
      }
    } catch (e) {
      dateRangeLabel = "Pick a date";
    }
  }

  return (
    <div className={cn("grid gap-2 whitespace-nowrap", className)}>
      <HoverCard open={showWarning}>
        <HoverCardTrigger asChild>
          <div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  id="date"
                  variant={"outline"}
                  className={cn(
                    "justify-between text-left flex",
                    !dateRange && "text-muted-foreground",
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {dateRangeLabel}
                  <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-[300px]" align="start">
                <DropdownMenuGroup>
                  <DropdownMenuItem
                    onClick={() => setDateRangePreset("last-24-hours")}
                  >
                    Last 24 hours
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setDateRangePreset("last-7-days")}
                  >
                    Last 7 days
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setDateRangePreset("last-30-days")}
                  >
                    Last 30 days
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setDateRangePreset("all-time")}
                  >
                    All time
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <Separator />
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>Custom</DropdownMenuSubTrigger>
                  <DropdownMenuSubContent>
                    <Calendar
                      initialFocus
                      mode="range"
                      defaultMonth={dateRange?.from}
                      selected={dateRange}
                      onSelect={(selected) => {
                        if (selected !== undefined) {
                          // Set the time of the from date to 00:00:00
                          if (selected.from) {
                            selected.from.setHours(0, 0, 0, 0);
                          }
                          // Set the time of the to date to 23:59:59
                          if (selected.to) {
                            selected.to.setHours(23, 59, 59, 999);
                          }
                          setDateRange(selected);
                        }
                      }}
                      numberOfMonths={2}
                    />
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </HoverCardTrigger>
        <HoverCardContent
          side="bottom"
          align="start"
          className="p-4 border rounded-lg shadow-lg"
        >
          Filter set to last 7 days.
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={closeWarning}
          >
            <X className="h-4 w-4 pt-1" />
          </Button>
        </HoverCardContent>
      </HoverCard>
    </div>
  );
}
