import { Checkbox } from "@/components/ui/checkbox";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { toast } from "@/components/ui/use-toast";
import { Project } from "@/models/models";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

const FormSchema = z.object({
  recipe_type_list: z.array(z.string()),
});

export default function DisableAnalytics({
  selectedProject,
}: {
  selectedProject: Project;
}) {
  const { accessToken } = useUser();
  const [checkedEval, setCheckedEval] = useState(
    selectedProject.settings?.run_evals === undefined
      ? true
      : selectedProject.settings?.run_evals,
  );
  const [checkedEvent, setCheckedEvent] = useState(
    selectedProject.settings?.run_event_detection === undefined
      ? true
      : selectedProject.settings?.run_event_detection,
  );
  const [checkedLangSent, setCheckedLangSent] = useState(
    selectedProject.settings?.run_sentiment_language === undefined
      ? true
      : selectedProject.settings?.run_sentiment_language,
  );

  const eventList: string[] = Object.keys(
    selectedProject?.settings?.events || {},
  );
  const formatedEventList = eventList.join(", ");
  const nbrEvents = eventList.length;

  useEffect(() => {
    if (accessToken) {
      const updateSettings = async () => {
        try {
          const response = await fetch(`/api/projects/${selectedProject.id}`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
              settings: {
                run_evals: checkedEval,
                run_event_detection: checkedEvent,
                run_sentiment_language: checkedLangSent,
              },
            }),
          });
          if (!response.ok) {
            throw new Error("Failed to update project settings");
          }
          toast({
            title: "Selection saved",
            description: "Project settings have been updated",
          });
        } catch (error) {
          toast({
            title: "There was an error",
            description:
              "We were unable to save your selection. Please try again later.",
          });
        }
      };
      updateSettings();
    }
  }, [
    checkedEval,
    checkedEvent,
    checkedLangSent,
    !checkedEval,
    !checkedEvent,
    !checkedLangSent,
  ]);

  const analytics = [
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

  return (
    <div>
      <div className="mb-4">
        <h3 className="text-lg font-bold tracking-tight mb-4">
          Disable analytics
        </h3>
        <p>You can disable or enable types of analytics for your project.</p>
      </div>
      {analytics.map((item) => (
        <div key={item.id} className="flex align-center">
          <Checkbox
            checked={
              item.id === "evaluation"
                ? checkedEval
                : item.id === "event_detection"
                  ? checkedEvent
                  : checkedLangSent
            }
            className="mt-1"
            onCheckedChange={(checked) => {
              const recipeTypeList = form.watch("recipe_type_list");
              if (checked) {
                form.setValue("recipe_type_list", [...recipeTypeList, item.id]);
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
                form.setValue(
                  "recipe_type_list",
                  recipeTypeList.filter((v) => v !== item.id),
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
          <div>
            <HoverCard openDelay={0} closeDelay={0}>
              <div className="flex">
                <span className="font-bold mb-4 ml-2">{item.label}</span>
                <HoverCardTrigger>
                  <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5 ml-2 mt-1" />
                </HoverCardTrigger>
              </div>
              <HoverCardContent>{item.description}</HoverCardContent>
            </HoverCard>
          </div>
        </div>
      ))}
    </div>
  );
}
