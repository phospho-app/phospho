"use client";

import Event from "@/components/events/event-analytics";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const eventId = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => router.back()} className="max-w-[10rem]">
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <Event eventId={eventId} />
    </>
  );
}
