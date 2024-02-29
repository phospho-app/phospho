"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialogCancel,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
// zustand state management
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Terminal } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { set, useForm } from "react-hook-form";
import * as z from "zod";

interface CreateNewProjectFormProps
  extends React.HTMLAttributes<HTMLDivElement> {
  setOpen: (open: boolean) => void;
}

const CreateNewProjectForm = ({ setOpen }: CreateNewProjectFormProps) => {
  // PropelAuth
  const { user, loading, accessToken } = useUser();

  // Zustand state management
  const setSelectedProject = navigationStateStore(
    (state) => state.setSelectedProject,
  );
  const projects = dataStateStore((state) => state.projects);
  const setProjects = dataStateStore((state) => state.setProjects);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const [isCreating, setIsCreating] = useState(false);
  const [isCreated, setIsCreated] = useState(false);
  const [creationError, setCreationError] = useState(false);

  const router = useRouter();

  const FormSchema = z.object({
    project_name: z.string({
      required_error: "Please enter a project name",
    }),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
  });

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    if (user) {
      setIsCreating(true);
      // Create a project object in the database with the URL
      const creation_response = await fetch(
        `/api/organizations/${selectedOrgId}/projects`,
        {
          method: "POST",
          headers: {
            Authorization: "Bearer " + accessToken,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            repo_url: "",
            project_name: data.project_name,
          }),
        },
      );

      const responseBody = await creation_response.json();

      console.log("responseBody :", responseBody);

      if (responseBody.project_name === data.project_name) {
        // Successfully created the project

        console.log("Project created");
        console.log(creation_response);

        // Change the selected project
        setSelectedProject(responseBody);
        // Add the project to the list of projects
        if (projects) {
          setProjects([responseBody, ...projects]);
        } else {
          setProjects([responseBody]);
        }

        // Close the dialog
        setIsCreated(true);
        setCreationError(false);
        setIsCreating(false);
        setOpen(false);

        // Redirect to the new project
        router.push(`/org/transcripts/tasks`);
      } else {
        // Display an error message
        setCreationError(true);
        setIsCreated(false);
        setIsCreating(false);
        console.log("Project creation failed");
      }
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <AlertDialogHeader>
          <AlertDialogTitle>
            <span className="mt-2 mb-2">Create a new project</span>
          </AlertDialogTitle>
        </AlertDialogHeader>

        {/* <AlertDialogDescription>
          <div className="mt-4">Chose a name for your new project</div>
        </AlertDialogDescription> */}

        <FormField
          control={form.control}
          name="project_name"
          render={({ field }) => (
            <FormItem>
              <div>Project Name</div>
              <FormControl>
                <Input
                  placeholder="Enter a project name"
                  maxLength={32}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <AlertDialogFooter>
          <AlertDialogCancel>Close</AlertDialogCancel>
          {!isCreating && !isCreated && (
            <Button type="submit">Create project</Button>
          )}
          {isCreating && (
            <>
              <Button type="button" disabled>
                Creating...
              </Button>
            </>
          )}
          {isCreated && (
            <>
              <Alert>
                <Terminal className="h-4 w-4" />
                <AlertTitle>Project created </AlertTitle>

                {/* <AlertDialogContent> */}

                {/* <AlertDialogAction onClick={() => { setOpen(false); }}> Close</AlertDialogAction> */}

                {/* </AlertDialogContent> */}
                {/* <AlertDescription>Refresh the page</AlertDescription> */}
              </Alert>
            </>
          )}
          {creationError && (
            <>
              <Alert>
                <Terminal className="h-4 w-4" />
                <AlertTitle className="text-red-500">
                  Project creation failed{" "}
                </AlertTitle>
                <AlertDescription>
                  Try using another name (see naming conventions)
                </AlertDescription>
              </Alert>
            </>
          )}
        </AlertDialogFooter>
      </form>
    </Form>
  );
};

export default CreateNewProjectForm;
