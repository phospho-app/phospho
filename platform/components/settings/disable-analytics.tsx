import { Checkbox } from "@/components/ui/checkbox";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { Project, ProjectSettings } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import useSWR from "swr";

function DisableAnalyticsCheckbox({
  checked,
  onCheckedChange,
  label,
  description,
}: {
  checked?: boolean;
  onCheckedChange: (checked: boolean) => void;
  label: string;
  description: string;
}) {
  return (
    <div className="flex flex-row items-center space-x-2">
      {checked !== undefined && (
        <Checkbox checked={checked} onCheckedChange={onCheckedChange} />
      )}
      <HoverCard openDelay={0} closeDelay={0}>
        <div>{label}</div>
        <div>
          <HoverCardTrigger>
            <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5" />
          </HoverCardTrigger>
        </div>
        <HoverCardContent className="w-80" side="right">
          {description}
        </HoverCardContent>
      </HoverCard>
    </div>
  );
}

export default function AnalyticsSettings() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const {
    data: selectedProject,
    mutate: mutateSelectedProject,
  }: {
    data: Project;
    mutate: (data: Project, options?: { revalidate: boolean }) => void;
  } = useSWR(
    project_id
      ? [`/api/projects/${project_id}`, accessToken, "update_settings"]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "GET").then((res) => {
        console.log("res", res);
        return res;
      }),
    {
      keepPreviousData: true,
    },
  );

  const eventList: string[] = Object.keys(
    selectedProject?.settings?.events || {},
  );
  const formatedEventList = eventList.join(", ");
  const nbrEvents = eventList.length;

  const handleChecked = async (updatedSettings?: ProjectSettings) => {
    if (!accessToken) return;
    if (!project_id) return;
    if (!selectedProject) return;
    if (!updatedSettings) return;
    mutateSelectedProject(
      {
        ...selectedProject,
        settings: updatedSettings,
      },
      {
        revalidate: false,
      },
    );
    fetch(`/api/projects/${project_id}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        settings: updatedSettings,
      }),
    }).then(async (response) => {
      if (!response.ok) {
        toast({
          title: "Error",
          description: "An error occurred while updating the settings.",
        });
        return;
      }
      const updatedProject = (await response.json()) as Project;
      mutateSelectedProject(updatedProject);
      toast({
        title: "Settings updated",
        description: "Your next logs will be updated with the new settings.",
      });
    });
  };

  return (
    <>
      <div>
        <div className="mb-4">
          <h2 className="text-2xl font-bold tracking-tight mb-1">
            Automatic analytics
          </h2>
          <p className="text-sm text-muted-foreground">
            The following analytics are automatically computed on logged
            content.
          </p>
        </div>
        <div className="space-y-1.5">
          <DisableAnalyticsCheckbox
            label="Event detection"
            description={`Detect if the setup events are present: ${formatedEventList}. ${nbrEvents} credits per user message, 1 per event.`}
            checked={selectedProject?.settings?.run_event_detection}
            onCheckedChange={() => {
              if (selectedProject?.settings?.run_event_detection === undefined)
                return;
              const updatedSettings = {
                ...selectedProject?.settings,
                run_event_detection:
                  !selectedProject.settings.run_event_detection,
              };
              handleChecked(updatedSettings);
            }}
          />
          <DisableAnalyticsCheckbox
            label="Sentiment"
            description="Recognize the sentiment (positive, negative) of the user message. 1 credit per user message."
            checked={selectedProject?.settings?.run_sentiment}
            onCheckedChange={() => {
              if (selectedProject?.settings?.run_sentiment === undefined)
                return;
              const updatedSettings = {
                ...selectedProject?.settings,
                run_sentiment: !selectedProject.settings.run_sentiment,
              };
              handleChecked(updatedSettings);
            }}
          />
          <DisableAnalyticsCheckbox
            label="Language"
            description="Detect the language of the user message. 1 credit per user message."
            checked={selectedProject?.settings?.run_language}
            onCheckedChange={() => {
              if (selectedProject?.settings?.run_language === undefined) return;
              const updatedSettings = {
                ...selectedProject?.settings,
                run_language: !selectedProject.settings.run_language,
              };
              handleChecked(updatedSettings);
            }}
          />
        </div>
      </div>
      <div className="mb-4">
        <h2 className="text-2xl font-bold tracking-tight mb-1">
          Monthly analytics threshold
        </h2>
        <p className="text-sm text-muted-foreground">
          If enabled, this stops analytics when more than the specified number
          of messages are processed in a month. The counter resets on the first
          day of each month.
        </p>
      </div>
      <div className="space-y-1.5">
        <div className="flex flex-row items-center space-x-2">
          <Checkbox
            checked={selectedProject?.settings?.tasks_threshold_enabled}
            onCheckedChange={() => {
              if (
                selectedProject?.settings?.tasks_threshold_enabled === undefined
              )
                return;
              const updatedSettings = {
                ...selectedProject?.settings,
                tasks_threshold_enabled:
                  !selectedProject.settings.tasks_threshold_enabled,
              };
              handleChecked(updatedSettings);
            }}
          />
          <span>Enable monthly analytics threshold</span>
        </div>
        {selectedProject?.settings?.tasks_threshold_enabled && (
          <div className="flex flex-row items-center space-x-2">
            <span>Max: </span>
            <Input
              className="max-w-[10rem]"
              type="number"
              value={selectedProject?.settings?.tasks_threshold_value}
              min={0}
              onChange={(e) => {
                if (selectedProject?.settings === undefined) return;
                if (!e.target.value) return;
                const thresholdValue = parseInt(e.target.value);
                const updatedSettings = {
                  ...selectedProject?.settings,
                  tasks_threshold_value: thresholdValue,
                };
                handleChecked(updatedSettings);
              }}
            />
            <span>processed user messages per month</span>
          </div>
        )}
      </div>
    </>
  );
}
