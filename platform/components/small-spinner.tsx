import { Loader2 } from "lucide-react";

export const Icons = {
  spinner: Loader2,
};

export default function SmallSpinner() {
  return (
    <>
      <div className="flex flex-col items-center justify-center h-60">
        <Icons.spinner className="h-4 w-4 animate-spin" />
      </div>
    </>
  );
}
