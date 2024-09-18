import { SheetOverlay } from "../ui/sheet";
import SessionOverview from "./session";

function SessionPreview({
  setOpen,
  session_id,
}: {
  setOpen: (open: boolean) => void;
  session_id: string | null;
}) {
  if (!session_id) {
    return null;
  }

  return (
    <>
      <SessionOverview session_id={session_id} />
    </>
  );
}

export { SessionPreview };
