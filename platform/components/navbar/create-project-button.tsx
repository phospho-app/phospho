import CreateProjectDialog from "@/components/projects/create-project-form";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function CreateProjectButton() {
  const [open, setOpen] = useState(false);

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="default" className="w-full bg-primary">
          Create new project
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent className="md:w-1/3">
        <CreateProjectDialog setOpen={setOpen}></CreateProjectDialog>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default CreateProjectButton;
