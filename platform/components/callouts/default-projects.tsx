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
    targetProjectId: string | undefined,
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
    console.log("targetProjectId", targetProjectId);
    //Create default project for orgID
    fetch(`/api/organizations/${selectedOrgId}/create-default-project`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        target_project_id: targetProjectId,
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 custom-plot min-w-full">
        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Biology teacher</CardTitle>
            <CardDescription>Educative ChatBot for students</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button
              className="items-center"
              onClick={() =>
                CreateDefaultProject(
                  "436a6aa53b8c49fe95cadc6297bcd6ec",
                  setOpen,
                )
              }
            >
              Use this project <Microscope className="h-4 w-4 ml-2" />{" "}
            </Button>
          </CardFooter>
        </Card>

        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>History teacher</CardTitle>
            <CardDescription>Educative ChatBot for students</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button
              className="items-center"
              onClick={() =>
                CreateDefaultProject(
                  "4feeb60f97834502b8af822c09a43d17",
                  setOpen,
                )
              }
            >
              Use this project <BookMarked className="h-4 w-4 ml-2" />{" "}
            </Button>
          </CardFooter>
        </Card>

        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Doctor</CardTitle>
            <CardDescription>Assistant ChatBot</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button
              className="items-center"
              onClick={() =>
                CreateDefaultProject(
                  "b85f4086435a425b8b1cca4d0988e0c1",
                  setOpen,
                )
              }
            >
              Use this project <Stethoscope className="h-4 w-4 ml-2" />{" "}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </AlertDialogContent>
  );
};
