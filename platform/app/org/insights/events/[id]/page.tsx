"use client";

import Event from "@/components/insights/events/EventAnalytics";
import { Button } from "@/components/ui/Button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const eventId = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => router.back()}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <Event eventId={eventId} />
    </>
  );
}
