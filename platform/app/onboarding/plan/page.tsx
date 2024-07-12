"use client";

import FullPageLoader from "@/components/full-page-loader";
import Pricing from "@/components/settings/pricing";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useSearchParams } from "next/navigation";
import { redirect, useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  // This page is no longer used

  redirect("/");
  return;

  const router = useRouter();

  // This page is used during the onboarding for the user to pick a plan.
  // It is also used as a paywall when the user tries to access a page that
  // requires a plan.

  // It is disbaled in preview mode
  // In this case, users are redirected to the root page

  // This page is used during the onboarding for the user to pick a plan.
  // It is also used as a paywall when the user tries to access a page that
  // requires a plan.

  // It is disbaled in preview mode
  // In this case, users are redirected to the root page
  if (process.env.NEXT_PUBLIC_APP_ENV === "preview") {
    router.push("/org/transcripts/tasks");
  }

  if (process.env.NEXT_PUBLIC_APP_ENV === "preview") {
    return <FullPageLoader />;
  }

  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect");
  // if redirect=true, then the user is trying to access a page that requires a plan
  // The tagline will be different in this case
  const tagline =
    redirectParam === "true"
      ? "phospho billing is evolving. Please pick a plan to continue."
      : "You're almost there! Please pick a plan to get started with phospho.";

  return (
    <>
      <Card className="mb-3">
        <CardHeader>
          <h2 className="text-2xl font-bold">One more thing...</h2>
        </CardHeader>
        <CardContent>
          <p>{tagline}</p>
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
