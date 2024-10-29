"use client";

import {
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
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
// zustand state management
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Plus, UserRound } from "lucide-react";
import { useForm } from "react-hook-form";
import useSWR, { mutate } from "swr";
import * as z from "zod";

import { Button } from "../ui/button";

const ExcludeUsersDialog = ({
  setOpen,
  projectToEdit,
}: {
  setOpen: (open: boolean) => void;
  projectToEdit?: Project;
}) => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const excludedUsers = selectedProject?.settings?.excluded_users || [];

  console.log("excludedUsers", excludedUsers);

  const FormSchema = z.object({
    user_id: z.string({
      required_error: "Please enter a user id",
    }),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
  });

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    const updatedProject = {
      ...selectedProject,
      settings: {
        ...selectedProject.settings,
        excluded_users: [...excludedUsers, data.user_id],
      },
    };
    console.log("updatedProject", updatedProject);
    // call the API endpoint
    await fetch(`/api/projects/${project_id}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        project_name: updatedProject.project_name,
        settings: updatedProject.settings,
      }),
    }).then(async () => {
      mutate([`/api/projects/${project_id}`, accessToken], async () => {
        return { project: selectedProject };
      });
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <AlertDialogHeader>
          {projectToEdit && <AlertDialogTitle>Exclude users</AlertDialogTitle>}
        </AlertDialogHeader>

        <div className="flex flex-row space-x-2">
          <FormField
            control={form.control}
            name="user_id"
            render={({ field }) => (
              <FormItem>
                <div>User id</div>
                <FormControl>
                  <Input
                    placeholder="Enter a user id"
                    maxLength={32}
                    {...field}
                    autoFocus
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" variant="default">
            <Plus className="size-4 mr-2" />
          </Button>
        </div>
        {excludedUsers.length > 0 && (
          <div className="flex flex-col space-y-2">
            Excluded users:
            {excludedUsers.map((user_id) => (
              <div key={user_id} className="flex items-center space-x-2">
                <UserRound className="w-6 h-6" />
                <div>{user_id}</div>
              </div>
            ))}
          </div>
        )}
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => setOpen(false)}>
            Close
          </AlertDialogCancel>
        </AlertDialogFooter>
      </form>
    </Form>
  );
};

export default ExcludeUsersDialog;
