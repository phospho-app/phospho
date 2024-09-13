"use client";

import { CustomPlot } from "@/components/clusters/clusters-plot";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BookOpenText, Boxes } from "lucide-react";
import Link from "next/link";

export default function Page() {
  return (
    <>
      <Card className="flex flex-col items-center max-w-full md:w-1/2 md:max-w-1/2">
        <CardHeader className="w-full flex flex-row">
          <Boxes className="mr-4 h-28 w-28 hover:text-green-500 transition-colors" />
          <div>
            <CardTitle className="mb-2">
              Use the phospho <span className="text-green-500">clustering</span>{" "}
              to uncover topics, user segments, and outliers.
            </CardTitle>
            <CardDescription>
              Go to the <b>clustering tab</b> to run your first clustering.
            </CardDescription>
          </div>
        </CardHeader>
        <CustomPlot dummyData={true} />
        <div className="flex space-x-4 w-full px-2 pb-2">
          <div className="flex-1">
            <Link href="/org">
              <Button variant="outline" className="w-full">
                <BookOpenText className="w-4 h-4 mr-1" />
                Explore transcripts first
              </Button>
            </Link>
          </div>
          <div className="flex-auto">
            <Link href="/org/insights/clusters">
              <Button variant="default" className="w-full">
                <Boxes className="w-4 h-4 mr-1" />
                Run clustering
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </>
  );
}
