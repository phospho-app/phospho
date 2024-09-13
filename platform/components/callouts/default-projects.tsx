import { X } from "lucide-react";

import {
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";

export const DefaultProjects = ({
  handleClose,
}: {
  handleClose: () => void;
}) => {
  return (
    <AlertDialogContent className="md:h-3/4 md:max-w-3/4 flex flex-col justify-between">
      <AlertDialogHeader>
        <div className="flex justify-between">
          <div className="flex flex-col space-y-2 w-full">
            <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
              Choose a project
            </AlertDialogTitle>
          </div>
          <X onClick={handleClose} className="cursor-pointer h-8 w-8" />
        </div>
      </AlertDialogHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 custom-plot min-w-full">
        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Biology teacher</CardTitle>
            <CardDescription>Educative ChatBot for students</CardDescription>
          </CardHeader>
        </Card>

        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>History teacher</CardTitle>
            <CardDescription>Educative ChatBot for students</CardDescription>
          </CardHeader>
        </Card>

        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Doctor</CardTitle>
            <CardDescription>Assistant ChatBot</CardDescription>
          </CardHeader>
        </Card>
      </div>
    </AlertDialogContent>
  );
};
