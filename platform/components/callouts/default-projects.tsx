import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { BookMarked, Microscope, Stethoscope, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useSWRConfig } from "swr";

import {
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { Button } from "../ui/button";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";

export const DefaultProjects = ({
  handleClose,
  setOpen,
}: {
  handleClose: () => void;
  setOpen: (value: boolean) => void;
}) => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { user, accessToken } = useUser();
  const router = useRouter();
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const toast = useToast();
  const { mutate } = useSWRConfig();
  const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  async function CreateDefaultProject(
    templateName: "history" | "animals" | "medical" | undefined,
    setOpen: (value: boolean) => void,
  ) {
    setOpen(false);
    if (!selectedOrgId) {
      // fetch the org id from the user
      const orgId = user?.getOrgs()[0].orgId;
      if (orgId) {
        setSelectedOrgId(orgId);
      } else {
        // if the user has no orgs, redirect to the auth
        router.push("/");
      }
    }
    //Create default project for orgID
    fetch(`/api/organizations/${selectedOrgId}/create-default-project`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        template_name: templateName,
      }),
    }).then(async (response) => {
      const responseBody = await response.json();
      if (responseBody.id !== undefined) {
        toast.toast({
          title: "We are creating your default project",
          description: "You will be redirected in a few seconds.",
        });
        await delay(1000);
        mutate([`/api/organizations/${selectedOrgId}/projects`, accessToken]);
        await delay(1000);
        setproject_id(responseBody.id);
        router.push(`/org`);
      } else {
        toast.toast({
          title: "Error when creating project",
          description: responseBody.error,
        });
      }
    });
  }
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 custom-plot min-w-full h-full">
        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Biology teacher</CardTitle>
            <CardDescription>Educative ChatBot for students</CardDescription>
          </CardHeader>
          <CardFooter>
            <div className="w-full flex justify-end">
              <Button
                className="flex justify-end mt-4"
                onClick={() => CreateDefaultProject("animals", setOpen)}
              >
                Explore project <Microscope className="h-4 w-4 ml-2" />{" "}
              </Button>
            </div>
          </CardFooter>
        </Card>

        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>History teacher</CardTitle>
            <CardDescription>Educative ChatBot for students</CardDescription>
          </CardHeader>
          <CardFooter>
            <div className="w-full flex justify-end">
              <Button
                className="flex justify-end mt-4"
                onClick={() => CreateDefaultProject("history", setOpen)}
              >
                Explore project <BookMarked className="h-4 w-4 ml-2" />{" "}
              </Button>
            </div>
          </CardFooter>
        </Card>

        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Doctor</CardTitle>
            <CardDescription>Assistant ChatBot</CardDescription>
          </CardHeader>
          <CardFooter>
            <div className="w-full flex justify-end">
              <Button
                className="flex justify-end"
                onClick={() => CreateDefaultProject("medical", setOpen)}
              >
                Explore project <Stethoscope className="h-4 w-4 ml-2" />{" "}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </AlertDialogContent>
  );
};
