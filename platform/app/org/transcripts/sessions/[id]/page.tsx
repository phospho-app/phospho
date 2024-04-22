"use client";

import Session from "@/components/transcripts/sessions/session";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const session_id = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => router.back()}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <Session session_id={session_id} />
    </>
  );
}
