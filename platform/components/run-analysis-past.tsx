import { DatePickerWithRange } from "@/components/date-range";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { ChevronRight, PlayIcon, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import FilterComponent from "./filters";
import { Spinner } from "./small-spinner";
import { toast } from "./ui/use-toast";
import UpgradeButton from "./upgrade-button";

const FormSchema = z.object({
  recipe_type_list: z.array(z.string()),
});

const RunAnalysisInPast = ({
  totalNbTasks,
}: {
  totalNbTasks: number | null | undefined;
}) => {
  const router = useRouter();
  const { accessToken } = useUser();
  const [checkedEval, setCheckedEval] = useState(true);
  const [checkedEvent, setCheckedEvent] = useState(true);
  const [checkedLangSent, setCheckedLangSent] = useState(true);
  const [totalAnalytics, setTotalAnalytics] = useState(0);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const hobby = orgMetadata?.plan === "hobby";

  const [loading, setLoading] = React.useState(false);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const project_id = selectedProject?.id;
  const eventList: string[] = Object.keys(
    selectedProject?.settings?.events || {},
  );
  const formatedEventList = eventList.join(", ");
  const nbrEvents = eventList.length;

  React.useEffect(() => {
    if (totalNbTasks) {
      setTotalAnalytics(
        ((checkedEval ? 1 : 0) +
          (checkedEvent ? nbrEvents : 0) +
          (checkedLangSent ? 2 : 0)) *
          totalNbTasks,
      );
    } else {
      setTotalAnalytics(0);
    }
  }, [checkedEval, checkedEvent, checkedLangSent, nbrEvents, totalNbTasks]);

  const form_choices = [
    {
      id: "evaluation",
      label: "Evaluation",
      description:
        "Automatically label tasks as a Success or Failure. 1 credit per task.",
    },
    {
      id: "event_detection",
      label: "Event detection",
      description:
        "Detect if the setup events are present: " +
        formatedEventList +
        ". " +
        nbrEvents +
        " credits per tasks, one per event.",
    },
    {
      id: "sentiment_language",
      label: "Sentiment & language",
      description:
        "Recognize the sentiment (positive, negative) and the language of the user's task input. 2 credits per task.",
    },
  ] as const;

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      recipe_type_list: ["evaluation", "event_detection", "sentiment_language"],
    },
  });

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    setLoading(true);
    // call the API endpoint
    const response = await fetch(`/api/recipes/${project_id}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        recipe_type_list: data.recipe_type_list,
        filters: dataFilters,
      }),
    });

    // Redirect to the home page
    router.push("/");

    if (!response.ok) {
      console.log("Error: ", response);
      toast({
        title: "Checkout Error - Please try again later",
        description: `Details: ${response.status} - ${response.statusText}`,
      });
      return;
    }

    toast({
      title: "Your analytics are running 🚀",
      description:
        "This may take a few minutes. Feel free to reach out - we're here to help.",
    });
  }

  return (
    <Sheet>
      <SheetTrigger>
        <Button variant={"outline"}>
          <Sparkles className="text-green-500 h-4 w-4 mr-2" />
          Detect
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </SheetTrigger>
      <SheetContent className="md:w-1/2 overflow-auto">
        <SheetTitle>Run analysis on past data</SheetTitle>
        <SheetDescription>
          Get events, flags, language, and sentiment labels.
        </SheetDescription>
        <Separator className="my-8" />
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <FormField
              control={form.control}
              name="recipe_type_list"
              render={() => (
                <FormItem>
                  <div className="mb-8">
                    <FormLabel className="text-base">
                      Select analytics to run on the data of the project '
                      {selectedProject?.project_name}'
                    </FormLabel>
                  </div>
                  <div className="flex flex-wrap">
                    <DatePickerWithRange className="mr-2" />
                    <FilterComponent variant="tasks" />
                  </div>
                  {form_choices.map((item) => (
                    <FormField
                      key={item.id}
                      control={form.control}
                      name="recipe_type_list"
                      render={({ field }) => {
                        return (
                          <FormItem
                            key={item.id}
                            className="flex flex-row items-center space-x-3 space-y-4 py-1"
                          >
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(item.id)}
                                className="mt-4"
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    field.onChange([...field.value, item.id]);
                                    if (item.id === "evaluation") {
                                      setCheckedEval(true);
                                    }
                                    if (item.id === "event_detection") {
                                      setCheckedEvent(true);
                                    }
                                    if (item.id === "sentiment_language") {
                                      setCheckedLangSent(true);
                                    }
                                  } else {
                                    field.onChange(
                                      field.value?.filter(
                                        (value) => value !== item.id,
                                      ),
                                    );
                                    if (item.id === "evaluation") {
                                      setCheckedEval(false);
                                    }
                                    if (item.id === "event_detection") {
                                      setCheckedEvent(false);
                                    }
                                    if (item.id === "sentiment_language") {
                                      setCheckedLangSent(false);
                                    }
                                  }
                                }}
                              />
                            </FormControl>
                            <FormLabel className="font-normal">
                              <HoverCard openDelay={0} closeDelay={0}>
                                <div className="flex flex-row space-x-2">
                                  <span>{item.label}</span>
                                  <HoverCardTrigger>
                                    <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5" />
                                  </HoverCardTrigger>
                                </div>
                                <HoverCardContent side="right" className="w-96">
                                  <div className="p-1 flex flex-col space-y-0">
                                    <div className="font-bold">
                                      {item.label}
                                    </div>
                                    <div>{item.description}</div>
                                  </div>
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
            {totalNbTasks && (
              <div>
                We will run {totalAnalytics} analytics, on {totalNbTasks} tasks,
                for a total of {totalAnalytics} credits.
              </div>
            )}
            {hobby && (
              <div className="flex justify-end">
                <UpgradeButton tagline="Run now" green={false} />
              </div>
            )}
            {!hobby && totalNbTasks && totalNbTasks > 0 && (
              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={
                    form.formState.isSubmitted || form.formState.isSubmitting
                  }
                >
                  {loading && <Spinner className="mr-2" />}
                  {!loading && (
                    <PlayIcon className="h-4 w-4 mr-2 text-green-500" />
                  )}
                  Run now
                </Button>
              </div>
            )}
            {!totalNbTasks && (
              <div>
                <div>No tasks selected</div>
              </div>
            )}
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
};

export default RunAnalysisInPast;
