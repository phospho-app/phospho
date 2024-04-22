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
import { addDays, format } from "date-fns";
import { Calendar as CalendarIcon, ChevronDown } from "lucide-react";
import * as React from "react";
import { DateRange } from "react-day-picker";

import { Separator } from "./ui/separator";

export function DatePickerWithRange({
  className,
}: React.HTMLAttributes<HTMLDivElement>) {
  const dateRangePreset = navigationStateStore(
    (state) => state.dateRangePreset,
  );
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);
  const setDateRange = navigationStateStore((state) => state.setDateRange);

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
  }

  return (
    <div className={cn("grid gap-2", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            id="date"
            variant={"outline"}
            className={cn(
              "w-[300px] justify-between text-left font-normal flex",
              !dateRange && "text-muted-foreground",
            )}
          >
            <div className="flex flex-row">
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRangeLabel}
            </div>
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
            <DropdownMenuItem onClick={() => setDateRangePreset("last-7-days")}>
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
  );
}
