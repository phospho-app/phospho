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

  const [date, setDate] = React.useState<DateRange | undefined>({
    from: undefined,
    to: new Date(),
  });

  if (dateRangePreset === "last-24-hours") {
    setDate({
      from: addDays(new Date(), -1),
      to: new Date(),
    });
    setDateRangePreset(null);
  }
  if (dateRangePreset === "last-7-days") {
    setDate({
      from: addDays(new Date(), -7),
      to: new Date(),
    });
    setDateRangePreset(null);
  }
  if (dateRangePreset === "last-30-days") {
    setDate({
      from: addDays(new Date(), -30),
      to: new Date(),
    });
    setDateRangePreset(null);
  }
  if (dateRangePreset === "all-time") {
    setDate({
      from: undefined,
      to: new Date(),
    });
    setDateRangePreset(null);
  }

  return (
    <div className={cn("grid gap-2", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            id="date"
            variant={"outline"}
            className={cn(
              "w-[300px] justify-start text-left font-normal",
              !date && "text-muted-foreground",
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, "y-LLL-dd")} -{" "}
                  {format(date.to, "y-LLL-dd")}
                </>
              ) : (
                format(date.from, "y-LLL-dd")
              )
            ) : (
              <span>Pick a date</span>
            )}
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
                defaultMonth={date?.from}
                selected={date}
                onSelect={setDate}
                numberOfMonths={2}
              />
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
