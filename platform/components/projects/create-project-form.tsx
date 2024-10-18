"use client";

import { Icons } from "@/components/small-spinner";
import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { Project, ProjectsData } from "@/models/models";
// zustand state management
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { BriefcaseBusiness } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import * as z from "zod";

const CreateProjectDialog = ({
  setOpen,
  projectToEdit,
}: {
  setOpen: (open: boolean) => void;
  projectToEdit?: Project;
}) => {
  const { accessToken } = useUser();
  const { mutate } = useSWRConfig();
  const { toast } = useToast();

  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  const [isCreating, setIsCreating] = useState(false);
  const [isCreated, setIsCreated] = useState(false);
  const router = useRouter();

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

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
    if (
      responseBody.project_name.slice(0, projectName.length) === projectName
    ) {
      // Change the selected project
      mutate(
        [`/api/organizations/${selectedOrgId}/projects`, accessToken],
        async (data: ProjectsData | undefined) => {
          return { projects: [responseBody, data?.projects] };
        },
      );
      setproject_id(responseBody.id);
      setIsCreated(true);
      setIsCreating(false);
      setOpen(false);
      // Redirect to the new project
      router.push(`/org/transcripts`);
    } else {
      console.log(
        "project_name",
        responseBody.project_name.slice(0, projectName.length),
      );
      console.log("project_name", responseBody.project_name);
      console.log("project_name", projectName);
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
    }).then(async () => {
      mutate([`/api/projects/${projectToEdit.id}`, accessToken], async () => {
        return { project: projectToEdit };
      });
      // Also mutate the project list
      mutate(
        [`/api/organizations/${selectedOrgId}/projects`, accessToken],
        async (data: ProjectsData | undefined) => {
          if (!data) {
            return { projects: [projectToEdit] };
          }
          // Find the project to edit
          const index = data.projects.findIndex(
            (project: Project) => project.id === projectToEdit.id,
          );
          // Replace the project
          if (index === -1) {
            return data;
          }

          const updatedProjects = [
            ...data.projects.slice(0, index),
            projectToEdit,
            ...data.projects.slice(index + 1),
          ];
          return { projects: updatedProjects };
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
            <AlertDialogTitle>
              <div className="flex flex-row items-center">
                <BriefcaseBusiness className="w-6 h-6 mr-2" />
                Create a new project
              </div>
            </AlertDialogTitle>
          )}
          {projectToEdit && (
            <AlertDialogTitle>
              Edit project &quot;{projectToEdit.project_name}&quot;
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
          <AlertDialogCancel onClick={() => setOpen(false)}>
            Close
          </AlertDialogCancel>
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
                <Icons.spinner className="mr-1 size-4 animate-spin" />
                Create project
              </AlertDialogAction>
            )}
          </div>
        </AlertDialogFooter>
      </form>
    </Form>
  );
};

export default CreateProjectDialog;
