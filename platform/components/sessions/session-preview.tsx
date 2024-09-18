import { ChevronRight } from "lucide-react";
import Link from "next/link";

import { Button } from "../ui/button";
import { SessionStats, SessionTranscript } from "./session";

function SessionPreview({
  session_id,
}: {
  setOpen: (open: boolean) => void;
  session_id: string | null;
}) {
  if (!session_id) {
    return null;
  }

  return (
    <div className="flex flex-col space-y-2">
      <SessionStats session_id={session_id} />
      <div className="flex w-full justify-start">
        <Link
          href={`/org/transcripts/sessions/${encodeURIComponent(session_id)}`}
        >
          <Button variant="secondary">
            Go to session page
            <ChevronRight />
          </Button>
        </Link>
      </div>
      <SessionTranscript session_id={session_id} />
    </div>
  );
}

export { SessionPreview };
