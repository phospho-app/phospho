import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export const Icons = {
  spinner: Loader2,
};

export function Spinner({ className, ...props }: { className?: string }) {
  return (
    <>
      <Icons.spinner className={cn("h-4 w-4 animate-spin", className)} />
    </>
  );
}

export function CenteredSpinner() {
  return (
    <>
      <div className="flex flex-col items-center justify-center h-60">
        <Spinner />
      </div>
    </>
  );
}
