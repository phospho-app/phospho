import CreateProjectDialog from "@/components/projects/create-project-form";
import { AlertDialog, AlertDialogContent } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { AlertDialogTrigger } from "@radix-ui/react-alert-dialog";
import { PlusIcon } from "lucide-react";
import { useState } from "react";

export function CreateProjectButton() {
  const [openProject, setOpenProject] = useState(false);

  return (
    <AlertDialog open={openProject} onOpenChange={setOpenProject}>
      <AlertDialogTrigger asChild>
        <div>
          <HoverCard openDelay={0} closeDelay={0}>
            <HoverCardTrigger asChild>
              <Button variant="outline" size="icon" className="py-1 h-8 w-8">
                <PlusIcon className="size-4" />
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
        <CreateProjectDialog setOpen={setOpenProject}></CreateProjectDialog>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default CreateProjectButton;
