import CreateNewProjectForm from "@/components/projects/create-project-form-light";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function AlertDialogProject() {
  const [open, setOpen] = useState(false);

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="outline" className="justify-start">
          Create a new project
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent className="md:w-1/3">
        <CreateNewProjectForm setOpen={setOpen}></CreateNewProjectForm>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default AlertDialogProject;
