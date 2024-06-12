import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Form, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { SentimentThreshold } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { EllipsisVertical, Settings } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import { z } from "zod";

export const SentimentSettings = ({}: {}) => {
  const [thresholdOpen, setThresholdOpen] = useState(false);
  const { mutate } = useSWRConfig();
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const tasksSorting = navigationStateStore((state) => state.tasksSorting);
  const tasksPagination = navigationStateStore(
    (state) => state.tasksPagination,
  );

  const { accessToken } = useUser();

  const selectedProject = dataStateStore((state) => state.selectedProject);
  const project_id = navigationStateStore((state) => state.project_id);

  const score = selectedProject?.settings?.sentiment_threshold?.score || 0.3;
  const magnitude =
    selectedProject?.settings?.sentiment_threshold?.magnitude || 0.6;

  const formSchema = z.object({
    score: z.number().min(0.05).max(1),
    magnitude: z.number().min(0.1).max(100),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      score: score,
      magnitude: magnitude,
    },
  });

  function toggleButton() {
    setThresholdOpen(!thresholdOpen);
  }

  async function onSubmit(values: z.infer<typeof formSchema>) {
    const { score, magnitude } = values;
    const threshold: SentimentThreshold = {
      score: score,
      magnitude: magnitude,
    };
    if (!selectedProject || !selectedProject.settings) {
      return;
    }
    selectedProject.settings.sentiment_threshold = threshold;

    const project_name = selectedProject.project_name;
    const settings = selectedProject.settings;
    fetch(`/api/projects/${project_id}`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_name: project_name,
        settings: settings,
      }),
    }).then(() => {
      mutate(
        project_id
          ? [
              `/api/projects/${project_id}/tasks`,
              accessToken,
              tasksPagination.pageIndex,
              JSON.stringify(dataFilters),
              JSON.stringify(tasksSorting),
            ]
          : null,
      );
      toggleButton();
    });
  }

  if (!selectedProject) {
    return <></>;
  }

  return (
    <DropdownMenu open={thresholdOpen} onOpenChange={setThresholdOpen}>
      <DropdownMenuTrigger>
        <Button variant="ghost" size={"icon"} onClick={toggleButton}>
          <EllipsisVertical className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-full">
        <DropdownMenuLabel className="flex flex-row items-center">
          <Settings className="w-4 h-4 mr-1" />
          Sentiment settings
        </DropdownMenuLabel>
        <div className="p-2">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="score"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="mr-2">
                      Score, Positive-Negative (0.05-1)
                    </FormLabel>
                    <Input
                      {...field}
                      type="number"
                      step="0.05"
                      className="input"
                      value={field.value}
                      onChange={(e) => {
                        field.onChange(e.target.valueAsNumber);
                      }}
                    />
                  </FormItem>
                )}
              ></FormField>
              <FormField
                control={form.control}
                name="magnitude"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="mr-2">
                      Magnitude, Neutral-Mixed (0.1-100)
                    </FormLabel>
                    <Input
                      {...field}
                      type="number"
                      step="0.1"
                      className="input"
                      value={field.value}
                      onChange={(e) => {
                        field.onChange(e.target.valueAsNumber);
                      }}
                    />
                  </FormItem>
                )}
              ></FormField>
              <Button
                type="submit"
                onClick={() => {
                  onSubmit(form.getValues());
                }}
                className="w-full"
              >
                Update
              </Button>
            </form>
          </Form>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
