"use client";

import { Icons } from "@/components/small-spinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialogAction,
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
import { useToast } from "@/components/ui/use-toast";
import { Project } from "@/models/models";
// zustand state management
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Terminal } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import * as z from "zod";

const CreateProjectDialog = ({
  setOpen,
  projectToEdit,
}: {
  setOpen: (open: boolean) => void;
  projectToEdit?: Project;
}) => {
  // PropelAuth
  const { accessToken } = useUser();
  const { mutate } = useSWRConfig();
  const { toast } = useToast();

  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const selectedProject = dataStateStore((state) => state.selectedProject);

  const [isCreating, setIsCreating] = useState(false);
  const [isCreated, setIsCreated] = useState(false);

  const router = useRouter();

  const FormSchema = z.object({
    project_name: z
      .string({
        required_error: "Please enter a project name",
      })
      .min(3, "Project name must be at least 3 characters long")
      .max(32, "Project name must be at most 32 characters long"),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      project_name: projectToEdit?.project_name || "",
    },
  });

  async function createProject(projectName: string) {
    setIsCreating(true);
    const creation_response = await fetch(
      `/api/organizations/${selectedOrgId}/projects`,
      {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: projectName,
        }),
      },
    );
    const responseBody = await creation_response.json();
    if (responseBody.project_name === projectName) {
      // Change the selected project
      setproject_id(responseBody.id);
      mutate(
        [`/api/organizations/${selectedOrgId}/projects`, accessToken],
        async (data: any) => {
          return { projects: [responseBody, data.projects] };
        },
      );
      setIsCreated(true);
      setIsCreating(false);
      setOpen(false);
      // Redirect to the new project
      router.push(`/org/transcripts/tasks`);
    } else {
      setIsCreated(false);
      setIsCreating(false);
      toast({
        title: "Project creation failed",
        description: "Contact us if the problem persists",
      });
    }
  }

  async function editProject(newProjectName: string) {
    if (!projectToEdit) {
      toast({
        title: "Project edit failed",
        description: "No project to edit",
      });
      return;
    }
    // Change the name
    projectToEdit.project_name = newProjectName;

    await fetch(`/api/projects/${projectToEdit.id}/`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(selectedProject),
    }).then(async (response) => {
      mutate(
        [`/api/projects/${projectToEdit.id}`, accessToken],
        async (data: any) => {
          return { project: projectToEdit };
        },
      );
      // Also mutate the project list
      mutate(
        [`/api/organizations/${selectedOrgId}/projects`, accessToken],
        async (data: any) => {
          // Find the project to edit
          const index = data.projects.findIndex(
            (project: Project) => project.id === projectToEdit.id,
          );
          // Replace the project
          data.projects[index] = projectToEdit;
          return { projects: data.projects };
        },
      );
    });
    setOpen(false);
  }

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    if (projectToEdit) {
      editProject(data.project_name);
    } else {
      createProject(data.project_name);
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <AlertDialogHeader>
          {(projectToEdit === null || projectToEdit === undefined) && (
            <AlertDialogTitle>Create a new project</AlertDialogTitle>
          )}
          {projectToEdit && (
            <AlertDialogTitle>
              Edit project "{projectToEdit.project_name}"
            </AlertDialogTitle>
          )}
        </AlertDialogHeader>

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
                  autoFocus
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <AlertDialogFooter>
          <AlertDialogCancel>Close</AlertDialogCancel>
          <div>
            {!isCreating &&
              !isCreated &&
              (projectToEdit === undefined || projectToEdit === null) && (
                <AlertDialogAction type="submit">
                  Create project
                </AlertDialogAction>
              )}
            {!isCreating && !isCreated && projectToEdit && (
              <AlertDialogAction type="submit">Save changes</AlertDialogAction>
            )}
            {isCreating && (
              <AlertDialogAction disabled>
                <Icons.spinner className="mr-1 h-4 w-4 animate-spin" />
              </AlertDialogAction>
            )}
          </div>
        </AlertDialogFooter>
      </form>
    </Form>
  );
};

export default CreateProjectDialog;
