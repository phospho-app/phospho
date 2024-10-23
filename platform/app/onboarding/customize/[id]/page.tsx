"use client";

import OnboardingProgress from "@/components/OnboardingProgress";
import { useSearchParams } from "next/navigation";

import AddEvents from "./add-events";

export default function Page({ params }: { params: { id: string } }) {
  // This page is called during onboarding, but also when the users clicks the
  // "Add suggested events" in the dashboard. In the latter case, there is
  // a redirect parameter in the query string. We use it to redirect the user
  // to the correct page after the onboarding is complete.
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");
  const redirectTo =
    redirect == "events" ? "/org/insights/events" : "/onboarding/clustering";

  const onboardingSteps = [
    {
      label: "Create an account",
      isActive: true,
      isCompleted: true,
    },
    {
      label: "Create project",
      isActive: true,
      isCompleted: true,
    },
    {
      label: "Customize",
      isActive: true,
      isCompleted: false,
    },
    {
      label: "Deep dive",
      isActive: false,
      isCompleted: false,
    },
  ];

  return (
    <>
      <OnboardingProgress steps={onboardingSteps} />
      <AddEvents project_id={params.id} redirectTo={redirectTo} />
    </>
  );
}
