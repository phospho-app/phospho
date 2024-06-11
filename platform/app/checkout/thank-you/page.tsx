"use client";

import { CenteredSpinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { useToast } from "@/components/ui/use-toast";
import { toast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

const items = [
  {
    id: "evaluation",
    label: "Evaluation",
    description: "Automatically label task as a Success or Failure.",
  },
  {
    id: "event_detection",
    label: "Event detection",
    description: "Detect if the setup events are present in the data.",
  },
  {
    id: "sentiment_language",
    label: "Sentiment & language",
    description:
      "Recognize the sentiment (positive, negative) and the language of the user's task input.",
  },
] as const;

const FormSchema = z.object({
  items: z.array(z.string()),
});

export function RunAnalyticsForm() {
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      items: ["evaluation", "event_detection", "sentiment_language"],
    },
  });

  function onSubmit(data: z.infer<typeof FormSchema>) {
    toast({
      title: "You submitted the following values:",
      description: (
        <pre className="mt-2 w-[340px] rounded-md bg-slate-950 p-4">
          <code className="text-white">{JSON.stringify(data, null, 2)}</code>
        </pre>
      ),
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
          control={form.control}
          name="items"
          render={() => (
            <FormItem>
              <div className="mb-8">
                <FormLabel className="text-base">
                  Select analytics to run on your data:
                </FormLabel>
              </div>
              {items.map((item) => (
                <FormField
                  key={item.id}
                  control={form.control}
                  name="items"
                  render={({ field }) => {
                    return (
                      <FormItem
                        key={item.id}
                        className="flex flex-row items-center space-x-3 space-y-0 py-1"
                      >
                        <FormControl>
                          <Checkbox
                            checked={field.value?.includes(item.id)}
                            onCheckedChange={(checked) => {
                              return checked
                                ? field.onChange([...field.value, item.id])
                                : field.onChange(
                                    field.value?.filter(
                                      (value) => value !== item.id,
                                    ),
                                  );
                            }}
                          />
                        </FormControl>
                        <FormLabel className="font-normal">
                          <HoverCard openDelay={0} closeDelay={0}>
                            <HoverCardTrigger>
                              <div className="flex flex-row space-x-2">
                                <span>{item.label}</span>
                                <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5" />
                              </div>
                            </HoverCardTrigger>
                            <HoverCardContent side="right" className="w-72">
                              <div className="p-1">{item.description}</div>
                            </HoverCardContent>
                          </HoverCard>
                        </FormLabel>
                      </FormItem>
                    );
                  }}
                />
              ))}
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="flex justify-between">
          <Link href="/">
            <Button variant="link" className="px-0">
              Later
            </Button>
          </Link>
          <Button type="submit">Run now</Button>
        </div>
      </form>
    </Form>
  );
}

export default function Page() {
  // This is a Thank you page displayed after a successful checkout

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
  const hasTasks: boolean | undefined = project_id
    ? hasTasksData?.has_tasks
    : false;

  return (
    <>
      {hasTasks === undefined && <CenteredSpinner />}
      {hasTasks === false && (
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
      )}
      {hasTasks && (
        <>
          <Card className={"container w-96"}>
            <CardHeader>
              <CardTitle className="py-2">
                <div className="font-bold">Welcome to phospho.</div>
              </CardTitle>
              <CardDescription className="text-sm flex flex-col space-y-2">
                <RunAnalyticsForm />
              </CardDescription>
            </CardHeader>
          </Card>
        </>
      )}
    </>
  );
}
