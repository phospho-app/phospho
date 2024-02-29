import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, Waves } from "lucide-react";

export function AlertDemo() {
  return (
    <Alert>
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>The project is in Alpha</AlertTitle>
      <AlertDescription className="mt-2">
        Desktop experience only
      </AlertDescription>
    </Alert>
  );
}
