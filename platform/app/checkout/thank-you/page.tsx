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
import Link from "next/link";
import { useRouter } from "next/navigation";

// This is a Thank you page displayed after a successful checkout

export default function Page() {
  const router = useRouter();
  const toast = useToast();

  function onBoogieClick() {
    toast.toast({
      title: "Your account activation is in progress 🚀",
      description:
        "You should see changes in a few minutes max. If not, please refresh the page. Contact us if anything - we're here to help.",
    });
    router.push("/");
  }

  return (
    <>
      <Card className={"container w-96"}>
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
      </Card>
    </>
  );
}
