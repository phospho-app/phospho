import { Button } from "@/components/ui/button";
import { CardHeader } from "@/components/ui/card";
import { FormControl, FormField, FormItem } from "@/components/ui/form";
import { Form } from "@/components/ui/form";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/use-toast";
import { generateSlug } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { PlusIcon } from "lucide-react";
import React from "react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Spinner } from "../small-spinner";

const FormSchema = z.object({
  version_id: z.string().min(2).max(30),
});

const CreateNewABTestButton = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const [popoverOpen, setPopoverOpen] = useState(false);

  async function onSubmit(values: z.infer<typeof FormSchema>) {
    setPopoverOpen(false);
    setABButtonClicked(true);
    // Call the API to create
    await fetch(`/api/projects/${project_id}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        settings: {
          ab_version_id: values.version_id,
        },
      }),
    }).then(() => {
      toast({
        title: "Version ID updated",
        description: "This new version_id will be added to your next logs",
      });
    });
    setABButtonClicked(false);
  }

  const [aBButtonClicked, setABButtonClicked] = useState(false);

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      version_id: generateSlug() ?? "",
    },
  });

  return (
    <>
      <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
        <div className="flex min-w-[10rem]">
          <PopoverTrigger asChild>
            <Button>
              <PlusIcon className="h-4 w-4 mr-2" />
              New AB Test
            </Button>
          </PopoverTrigger>
          {/* <Button onClick={clearABTest} className="ml-2">
            Clear AB Test
          </Button> */}
        </div>
        <PopoverContent align="start" className="w-96 h-120">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
              <CardHeader>
                <FormItem>
                  <FormField
                    control={form.control}
                    name="version_id"
                    render={({ field }) => (
                      <FormControl>
                        <Textarea
                          id="version_id"
                          placeholder={`Create a custom ID for your next AB test.`}
                          {...field}
                        />
                      </FormControl>
                    )}
                  />
                </FormItem>

                <Button
                  className="hover:bg-green-600"
                  type="submit"
                  disabled={aBButtonClicked || !form.formState.isValid}
                >
                  {aBButtonClicked && <Spinner className="mr-1" />}
                  Start new AB test
                </Button>
              </CardHeader>
            </form>
          </Form>
        </PopoverContent>
      </Popover>
    </>
  );
};

export default CreateNewABTestButton;
