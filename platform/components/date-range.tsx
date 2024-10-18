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
import {
  Calendar as CalendarIcon,
  ChevronDown,
  ChevronLeft,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import * as React from "react";

import { HoverCard, HoverCardContent, HoverCardTrigger } from "./ui/hover-card";
import { Separator } from "./ui/separator";

export function DatePickerWithRange({
  className,
}: {
  className?: React.HTMLAttributes<HTMLDivElement>;
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
    const showCondition = !warningShown && dateRangePreset === "last-7-days";
    if (showCondition) {
      setShowWarning(true);
      setWarningShowed(true);
    }
  }, [dateRangePreset, setWarningShowed, warningShown]);

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
    } catch {
      dateRangeLabel = "Pick a date";
    }
  }

  return (
    <div className={cn("", className)}>
      <HoverCard open={showWarning}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <HoverCardTrigger asChild>
              <Button
                id="date"
                variant={"outline"}
                className={cn(
                  "justify-between text-left flex min-w-[12rem]",
                  !dateRange && "text-muted-foreground",
                )}
              >
                <CalendarIcon className="mr-2 size-4" />
                {dateRangeLabel}
                <ChevronDown className="ml-2 size-4" />
              </Button>
            </HoverCardTrigger>
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
              <DropdownMenuItem onClick={() => setDateRangePreset("all-time")}>
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
        <HoverCardContent
          side="right"
          align="center"
          avoidCollisions={false}
          className="p-2 border rounded-lg shadow-lg m-0 text-xs text-background bg-foreground flex items-center cursor-pointer"
          onClick={closeWarning}
        >
          <ChevronLeft className="size-4 ml-2" /> Data is filtered by date range
          <X className="ml-1 h-3 w-3" />
        </HoverCardContent>
      </HoverCard>
    </div>
  );
}
