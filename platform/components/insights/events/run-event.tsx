"use client";

import ComingSoonAlert from "@/components/coming-soon";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import {
  DetectionEngine,
  DetectionScope,
  EventDefinition,
} from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import { z } from "zod";

export default function RunEvent({
  setOpen,
  eventToRun,
}: {
  setOpen: (open: boolean) => void;
  eventToRun: EventDefinition;
}) {
  // This is a form that lets you run an event detection on previous data
  // Component to create an event or edit an existing event

  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { mutate } = useSWRConfig();
  const { loading, accessToken } = useUser();
  const { toast } = useToast();

  // If we are editing an event, we need to pre-fill the form
  const formSchema = z.object({});

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {},
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    console.log("Submitting event:", values);
    if (!selectedProject) {
      console.log("Submit: No selected project");
      return;
    }
    if (!selectedProject.settings) {
      console.log("Submit: No selected project settings");
      return;
    }
  }

  console.log("form", form);

  return (
    <>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="font-normal space-y-4"
          key={`createEventForm_${eventToRun.id}`}
        >
          <SheetHeader>
            <SheetTitle className="text-xl">
              Run detection for event "{eventToRun.event_name}""
            </SheetTitle>
            <SheetDescription>
              This will run the event detection engine on already logged data.
            </SheetDescription>
          </SheetHeader>
          <Separator />
          <div className="flex-col space-y-2">
            <ComingSoonAlert />
          </div>
          <SheetFooter>
            <Button type="submit" disabled={loading}>
              Run detection
            </Button>
          </SheetFooter>
        </form>
      </Form>
    </>
  );
}
