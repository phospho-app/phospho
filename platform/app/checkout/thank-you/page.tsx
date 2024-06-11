"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import useSWR from "swr";

// This is a Thank you page displayed after a successful checkout

export default function Page() {
  const router = useRouter();
  const toast = useToast();
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  function onBoogieClick() {
    toast.toast({
      title: "We are activating your account 🚀",
      description:
        "You should see changes in a few minutes max. If not, please refresh the page. Contact us if anything - we're here to help.",
    });
    router.push("/");
  }

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  return (
    <>
      <Card className={"container w-96"}>
        {!hasTasks && (
          <>
            <CardHeader>
              <CardTitle className="font-bold">Thank you!</CardTitle>
              <CardDescription className="text-xl">
                You're now part of the phospho community.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <p>We can't wait to see what you'll build.</p>
            </CardContent>
            <CardFooter className="flex justify-center">
              <Button className="bg-green-500" onClick={onBoogieClick}>
                Let's boogie.
              </Button>
            </CardFooter>
          </>
        )}
        {hasTasks && (
          <>
            <CardHeader>
              <CardTitle className="font-bold">Welcome to phospho.</CardTitle>
              <CardDescription className="text-xl">
                Let's get you started.
              </CardDescription>
            </CardHeader>
            <CardFooter className="flex justify-between"></CardFooter>
          </>
        )}
      </Card>
    </>
  );
}
