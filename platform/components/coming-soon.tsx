import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { TrafficCone } from "lucide-react";

function ComingSoonAlert({ customMessage }: { customMessage?: string }) {
  if (!customMessage) {
    return (
      <>
        <Alert>
          <TrafficCone className="h-4 w-4" />
          <AlertTitle>Coming soon!</AlertTitle>
          <AlertDescription>
            We'll be shipping this feature shortly.{" "}
            <span className="italic">We're about to blow your mind.</span>
          </AlertDescription>
        </Alert>
      </>
    );
  }

  return (
    <>
      <Alert>
        <TrafficCone className="h-4 w-4" />
        <AlertTitle>Work in progress!</AlertTitle>
        <AlertDescription>{customMessage}</AlertDescription>
      </Alert>
    </>
  );
}

export default ComingSoonAlert;
