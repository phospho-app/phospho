import { Alert } from "@/components/ui/alert";
import { TrafficCone } from "lucide-react";

function ComingSoonAlert({ customMessage }: { customMessage?: string }) {
  if (!customMessage) {
    return (
      <>
        <Alert>
          <div className="flex flex-row items-center space-x-1">
            <TrafficCone className="size-4 mr-1" />
            <span className="text-sm font-semibold">Coming soon!</span>
            <span className="text-sm">
              We&apos;ll be shipping this feature shortly.
            </span>
            <span className="italic text-sm">
              We&apos;re about to blow your mind.
            </span>
          </div>
        </Alert>
      </>
    );
  }

  return (
    <>
      <Alert>
        <div className="flex flex-row items-center space-x-1">
          <TrafficCone className="size-4 mr-1" />
          <span className="text-sm font-semibold">Work in progress!</span>
          <span className="text-sm">{customMessage}</span>
        </div>
      </Alert>
    </>
  );
}

export default ComingSoonAlert;
