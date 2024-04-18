import CreateProjectDialog from "@/components/projects/create-project-form";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { PlusIcon } from "lucide-react";
import { useState } from "react";

export function CreateProjectButton() {
  const [open, setOpen] = useState(false);

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <div>
          <HoverCard openDelay={50} closeDelay={50}>
            <HoverCardTrigger asChild>
              <Button variant="outline" size="icon">
                <PlusIcon className="h-4 w-4" />
              </Button>
            </HoverCardTrigger>
            <HoverCardContent
              className="m-0 text-xs text-background bg-foreground"
              align="center"
              avoidCollisions={false}
            >
              <span>Create project</span>
            </HoverCardContent>
          </HoverCard>
        </div>
      </AlertDialogTrigger>
      <AlertDialogContent className="md:w-1/3">
        <CreateProjectDialog setOpen={setOpen}></CreateProjectDialog>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default CreateProjectButton;
