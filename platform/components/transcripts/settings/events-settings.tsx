import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { EventDefinition } from "@/models/models";
import { EllipsisVertical, PlusIcon, Sparkles } from "lucide-react";
import React from "react";

export const RunEventsSettings = ({
  eventArray,
  setSheetOpen,
  setSheetToOpen,
  setEventDefinition,
}: {
  eventArray: [string, EventDefinition][];
  setSheetOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setSheetToOpen: React.Dispatch<React.SetStateAction<string | null>>;
  setEventDefinition: React.Dispatch<
    React.SetStateAction<EventDefinition | null>
  >;
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical className="w-5 h-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuLabel>
          <div className="flex flex-row items-center">
            <Sparkles className="w-4 h-4 text-green-500 mr-1" />
            <div>Detect event</div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuGroup className="overflow-y-auto max-h-[20rem]">
          {eventArray.map(([, event_definition]) => {
            return (
              <DropdownMenuItem
                key={event_definition.event_name}
                onClick={(mouseEvent) => {
                  // This is used to avoid clicking on the row as well
                  mouseEvent.stopPropagation();
                  setEventDefinition(event_definition);
                  setSheetOpen(true);
                  setSheetToOpen("run");
                }}
              >
                {event_definition.event_name}
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuGroup>
        <DropdownMenuItem
          onClick={(mouseEvent) => {
            // This is used to avoid clicking on the row as well
            mouseEvent.stopPropagation();
            setSheetToOpen("edit");
            setSheetOpen(true);
            setEventDefinition(null);
          }}
        >
          <PlusIcon className="w-4 h-4 mr-1" />
          Add new event
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
