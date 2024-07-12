import { Checkbox } from "@/components/ui/Checkbox";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/HoverCard";
import { toast } from "@/components/ui/UseToast";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { useState } from "react";
import useSWR from "swr";

export default function DisableAnalytics() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const [checkedEval, setCheckedEval] = useState(
    selectedProject.settings?.run_evals,
  );
  const [checkedEvent, setCheckedEvent] = useState(
    selectedProject.settings?.run_event_detection,
  );
  const [checkedLanguage, setCheckedLanguage] = useState(
    selectedProject.settings?.run_language,
  );

  const [checkedSentiment, setCheckedSentiment] = useState(
    selectedProject.settings?.run_sentiment,
  );

  const eventList: string[] = Object.keys(
    selectedProject?.settings?.events || {},
  );
  const formatedEventList = eventList.join(", ");
  const nbrEvents = eventList.length;

  const handleChecked = (id: string) => {
    if (!accessToken) return;
    if (!selectedProject) return;
    if (!selectedProject.id) return;
    if (checkedEval === undefined) return;
    if (checkedEvent === undefined) return;
    if (checkedLanguage === undefined) return;
    if (checkedSentiment === undefined) return;
    const updateSettings = async () => {
      await fetch(`/api/projects/${selectedProject.id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          settings: {
            run_evals: id === "evaluation" ? !checkedEval : checkedEval,
            run_event_detection:
              id === "event_detection" ? !checkedEvent : checkedEvent,
            run_language:
              id === "language" ? !checkedLanguage : checkedLanguage,
            run_sentiment:
              id === "sentiment" ? !checkedSentiment : checkedSentiment,
          },
        }),
      }).then(() => {
        toast({
          title: "Settings updated",
          description: "Your next logs will be updated with the new settings.",
        });
      });
    };
    updateSettings();
  };

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
        " credits per tasks, 1 per event.",
    },
    {
      id: "sentiment",
      label: "Sentiment",
      description:
        "Recognize the sentiment (positive, negative) of the user's task input. 1 credit per task.",
    },
    {
      id: "language",
      label: "Language",
      description:
        "Detect the language of the user's task input. 1 credit per task.",
    },
  ] as const;

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-2xl font-bold tracking-tight mb-1">
          Automatic analytics
        </h2>
        <p className="text-sm text-muted-foreground">
          The following analytics are automatically computed on logged content.
        </p>
      </div>
      <div className="space-y-1.5">
        {analytics.map((item) => (
          <div key={item.id} className="flex flex-row items-center space-x-2">
            <Checkbox
              checked={
                item.id === "evaluation"
                  ? checkedEval
                  : item.id === "event_detection"
                    ? checkedEvent
                    : item.id === "sentiment"
                      ? checkedSentiment
                      : checkedLanguage
              }
              onCheckedChange={(checked) => {
                if (checked) {
                  if (item.id === "evaluation") {
                    setCheckedEval(true);
                  }
                  if (item.id === "event_detection") {
                    setCheckedEvent(true);
                  }
                  if (item.id === "sentiment") {
                    setCheckedSentiment(true);
                  }
                  if (item.id === "language") {
                    setCheckedLanguage(true);
                  }
                } else {
                  if (item.id === "evaluation") {
                    setCheckedEval(false);
                  }
                  if (item.id === "event_detection") {
                    setCheckedEvent(false);
                  }
                  if (item.id === "sentiment") {
                    setCheckedSentiment(false);
                  }
                  if (item.id === "language") {
                    setCheckedLanguage(false);
                  }
                }
                handleChecked(item.id);
              }}
            />
            <HoverCard openDelay={0} closeDelay={0}>
              <div>{item.label}</div>
              <div>
                <HoverCardTrigger>
                  <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5" />
                </HoverCardTrigger>
              </div>
              <HoverCardContent className="w-80">
                {item.description}
              </HoverCardContent>
            </HoverCard>
          </div>
        ))}
      </div>
    </div>
  );
}
