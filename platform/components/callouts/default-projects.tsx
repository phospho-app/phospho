import {
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  BookMarked,
  Microscope,
  Stethoscope,
  Telescope,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";

const DefaultProjects = ({
  handleClose,
  setOpen,
  redirect = "/org",
  earlyRedirect = false,
}: {
  handleClose?: () => void;
  setOpen: (value: boolean) => void;
  redirect?: string;
  earlyRedirect?: boolean;
}) => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { user, accessToken } = useUser();
  const router = useRouter();
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const toast = useToast();
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  if (!handleClose) {
    handleClose = () => {};
  }

  async function createDefaultProject(
    templateName: "history" | "animals" | "medical" | undefined,
  ) {
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
    toast.toast({
      title: "Creating example project ⌛︎",
      description: "This should be quick.",
    });
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
      if (!response.ok) {
        toast.toast({
          title: "Error when creating project",
          description: response.statusText,
        });
        return;
      }
      const responseBody = await response.json();
      if (responseBody.id !== undefined) {
        setproject_id(responseBody.id);
        if (!earlyRedirect) {
          router.push(redirect);
        }
      } else {
        toast.toast({
          title: "Error when creating project",
          description: "No project ID returned",
        });
      }
    });

    setOpen(false);
    if (earlyRedirect) {
      router.push(redirect);
    }
  }
  return (
    <AlertDialogContent className="md:h-3/4 md:max-w-3/4 flex flex-col justify-between overflow-y-auto max-h-[100dvh]">
      <AlertDialogHeader>
        <div className="flex justify-between space-x-2">
          <Telescope className="h-16 w-16 hover:text-green-500 transition-colors" />
          <div className="flex flex-col gap-y-2 w-full">
            <AlertDialogTitle className="text-2xl font-bold">
              Explore a project with example data
            </AlertDialogTitle>
            <AlertDialogDescription>
              These projects contain text data from AI apps. Discover what went
              right, and what went wrong during development.
            </AlertDialogDescription>
          </div>
          <X onClick={handleClose} className="cursor-pointer h-8 w-8" />
        </div>
      </AlertDialogHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 custom-plot min-w-full h-full">
        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-end">
          <CardHeader>
            <CardTitle>Taming an impatient AI</CardTitle>
            <CardDescription>
              Conversations about biology between students and an rude AI
              chatbot, that we make more and more patient.
            </CardDescription>
          </CardHeader>
          <div className="min-h-48 h-full w-full bg-secondary bg-gradient-to-tr from-green-800 to-blue-200 rounded-3xl"></div>
          <CardFooter>
            <div className="w-full flex justify-end">
              <Button
                variant="secondary"
                className="flex justify-end mt-4"
                onClick={() => createDefaultProject("animals")}
              >
                Explore project <Microscope className="size-4 ml-2" />{" "}
              </Button>
            </div>
          </CardFooter>
        </Card>
        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-end">
          <CardHeader>
            <CardTitle>Forgotten history</CardTitle>
            <CardDescription>
              An AI being quizzed about historical characters, that becomes more
              and more knowledgeable.
            </CardDescription>
          </CardHeader>
          <div className="min-h-48 h-full w-full bg-secondary bg-gradient-to-t from-pink-500 to-blue-400 rounded-3xl"></div>
          <CardFooter>
            <div className="w-full flex justify-end">
              <Button
                variant="secondary"
                className="flex justify-end mt-4"
                onClick={() => createDefaultProject("history")}
              >
                Explore project <BookMarked className="size-4 ml-2" />{" "}
              </Button>
            </div>
          </CardFooter>
        </Card>
        <Card className="rounded-lg shadow-md p-4 flex flex-col justify-end">
          <CardHeader>
            <CardTitle>Tricky medical questions</CardTitle>
            <CardDescription>
              A medical assistant answers concerns from various patients, but
              sometimes gives wrong answers.
            </CardDescription>
          </CardHeader>
          <div className="min-h-48 h-full w-full bg-secondary bg-gradient-to-r from-indigo-500 to-purple-700 rounded-3xl"></div>
          <CardFooter>
            <div className="w-full flex justify-end">
              <Button
                variant="secondary"
                className="flex justify-end mt-4"
                onClick={() => createDefaultProject("medical")}
              >
                Explore project <Stethoscope className="size-4 ml-2" />{" "}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </AlertDialogContent>
  );
};

export { DefaultProjects };
