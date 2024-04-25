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
import { Flag, ThumbsDown, ThumbsUp } from "lucide-react";
import React from "react";

const FilterComponent = ({}: React.HTMLAttributes<HTMLDivElement>) => {
  const setTasksColumnsFilters = navigationStateStore(
    (state) => state.setTasksColumnsFilters,
  );

  const state = navigationStateStore.getState();

  return (
    <div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline">Select filters</Button>
        </DropdownMenuTrigger>
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
                >
                  <ThumbsDown className="h-4 w-4 mr-2" />
                  <span>Failure</span>
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
