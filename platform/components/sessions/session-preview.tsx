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
      <SessionStats session_id={session_id} showGoToSession={true} />
      <SessionTranscript session_id={session_id} />
    </div>
  );
}

export { SessionPreview };
