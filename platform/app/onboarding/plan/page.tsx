"use client";

import Pricing from "@/components/settings/pricing";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function Page({ params }: { params: { id: string } }) {
  return (
    <>
      <Card className="mb-3">
        <CardHeader>
          <h2 className="text-2xl font-bold">One more thing...</h2>
        </CardHeader>
        <CardContent>
          <p>
            You're almost there! Please pick a plan to get started with phospho.
          </p>
        </CardContent>
      </Card>
      <Pricing
        currentPlan={null}
        selectedPlan={"pro"}
        proPlanTagline="Try for free"
        displayHobbyCTA={true}
      />
    </>
  );
}
