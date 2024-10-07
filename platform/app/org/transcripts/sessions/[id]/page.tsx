"use client";

import { SessionOverview } from "@/components/sessions/session";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const session_id = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => router.back()} className="max-w-[10rem]">
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <SessionOverview session_id={session_id} />
    </>
  );
}
