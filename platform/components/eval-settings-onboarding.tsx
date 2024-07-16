import { Button } from "@/components/ui/button";
import { Form, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { authFetcher } from "@/lib/fetcher";
import { EvaluationModel, EvaluationModelDefinition } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { AlertDialog, AlertDialogTitle } from "@radix-ui/react-alert-dialog";
import { Settings, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

import { Spinner } from "./small-spinner";
import { Textarea } from "./ui/textarea";

export const EvalSettingsOnboarding = ({
  setOpen,
}: {
  setOpen: (open: boolean) => void;
}) => {
  const [evalOpen, setEvalOpen] = useState(false);
  const [clicked, setClicked] = useState(false);
  const { accessToken } = useUser();

  const project_id = navigationStateStore((state) => state.project_id);

  const {
    data: evaluation_model,
    mutate: mutateEvaluation,
  }: { data: EvaluationModel; mutate: any } = useSWR(
    project_id ? [`/api/projects/${project_id}/evaluation`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const formSchema = z.object({
    prompt: z.string().max(1000),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      prompt:
        evaluation_model?.system_prompt ||
        "Answer positively when the interaction talks about ... and negatively when it does not.",
    },
  });

  function toggleButton() {
    setEvalOpen(!evalOpen);
  }

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setClicked(true);
    const { prompt } = values;
    if (!project_id) {
      return;
    }
    const payload: EvaluationModelDefinition = {
      project_id: project_id,
      system_prompt: prompt,
    };
    fetch(`/api/projects/${project_id}/evaluation`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ...payload }),
    }).then((response) => {
      mutateEvaluation(response.json());
      setClicked(false);
      toggleButton();
    });
  }

  if (!project_id || !prompt) {
    return <></>;
  }

  return (
    <AlertDialog>
      <AlertDialogTitle className="flex flex-row items-center">
        <Settings className="w-4 h-4 mr-1" />
        System prompt for evaluation
      </AlertDialogTitle>
      <div className="p-2">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="prompt"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Describe what a successful interaction is to you
                  </FormLabel>
                  <Textarea
                    className="h-40 w-full break-words"
                    {...field}
                    autoFocus
                  />
                </FormItem>
              )}
            ></FormField>
            <Button
              type="submit"
              className="w-full"
              disabled={clicked || !prompt || !form.formState.isValid}
            >
              {clicked && <Spinner className="mr-1" />}
              Update
            </Button>
          </form>
        </Form>
      </div>
      <X
        onClick={() => setOpen(false)}
        className="absolute top-2 right-2 cursor-pointer"
      />
    </AlertDialog>
  );
};
