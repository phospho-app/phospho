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

export default function Page() {
  // This page is displayed when the user canceled checkout
  const toast = useToast();
  const router = useRouter();

  return (
    <>
      <Card className="w-96">
        <CardHeader>
          <CardTitle className="font-bold">Second thoughts?</CardTitle>
          <CardDescription className="text-xl">That's ok.</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          <p>
            We'd be happy to learn more about your project and see what we can
            do to help.
          </p>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button
            variant="link"
            onClick={() => {
              router.push("/");
              toast.toast({
                title: "Fair enough 🤝",
                description:
                  "If you have any questions, feel free to reach out.",
              });
            }}
          >
            No, leave me alone
          </Button>
          <Link href="https://calendly.com/paul-louis-phospho">
            <Button variant="default" className="bg-green-600">
              Let's chat
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </>
  );
}
