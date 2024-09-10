import { TriangleAlert } from "lucide-react";

import {
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import { Button } from "./ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "./ui/card";
import UpgradeButton from "./upgrade-button";

export const Blockwall = ({ handleSkip }: { handleSkip: () => void }) => {
  return (
    <AlertDialogContent className="md:max-w-1/2 flex flex-col justify-between">
      <AlertDialogHeader>
        <div className="flex justify-between">
          <div className="flex flex-col space-y-2 w-full">
            <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
              One more thing...
            </AlertDialogTitle>
            <Card className="w-full border-red-500 bg-red-200">
              <CardTitle className="text-xl mt-2 ml-2 text-black">
                <div className="flex align-center">
                  <TriangleAlert className="mr-2" />
                  Your account is missing billing information
                </div>
              </CardTitle>
              <CardHeader>
                <CardDescription className="text-black">
                  Please add payment information to enable data analytics
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </AlertDialogHeader>

      <div className="text-muted-foreground mx-[5%]">
        <p>Add your info to access advanced analytics features:</p>
        <ul>
          <li> - Sentiment Analytics</li>
          <li> - Success/Failure flags</li>
          <li> - Custom event detection </li>
          <li> - Language Detection</li>
          <li> - Data Clustering</li>
        </ul>
      </div>
      <div className="mx-[5%] font-semibold">
        Enable analytics now to get 10$ of free credits 🎁
      </div>

      <div className="flex justify-between">
        <Button
          onClick={() => handleSkip()}
          variant={"link"}
          className="text-muted-foreground"
        >
          Ignore
        </Button>
        <div className="flex flex-col justify-center items-center">
          <UpgradeButton tagline="Enable Analytics" />
        </div>
      </div>
    </AlertDialogContent>
  );
};
