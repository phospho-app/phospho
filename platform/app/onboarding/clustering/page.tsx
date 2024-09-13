"use client";

import { CustomPlot } from "@/components/clusters/clusters-plot";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Page() {
  return (
    <>
      <Card className="flex flex-col items-center space-y-4 max-w-full md:w-1/2 md:max-w-1/2">
        <CardHeader className="w-full">
          <CardTitle>
            The phospho clustering groups similar messages or sessions
          </CardTitle>
          <CardDescription>
            Go to the <b>clustering tab</b> to run your first clustering.
          </CardDescription>
        </CardHeader>
        <CustomPlot dummyData={true} />
        <div className="h-2"></div>
      </Card>
    </>
  );
}
