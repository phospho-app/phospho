"use client";

import { EventDefinition } from "@/models/models";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import AboutYou from "./about-you";
import AddEvents from "./add-events";

export default function Page({ params }: { params: { id: string } }) {
  const [aboutYouValues, setAboutYouValues] = useState(null);
  const [customEvents, setCustomEvents] = useState<EventDefinition[] | null>(
    null,
  );
  const [phosphoTaskId, setPhosphoTaskId] = useState<string | null>(null);

  // This page is called during onboarding, but also when the users clicks the
  // "Add suggested events" in the dashboard. In the latter case, there is
  // a redirect parameter in the query string. We use it to redirect the user
  // to the correct page after the onboarding is complete.
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");
  const redirectTo = redirect == "events" ? "/org/insights/events" : "/org";

  return (
    <>
      {aboutYouValues === null && (
        <AboutYou
          project_id={params.id}
          setAboutYouValues={setAboutYouValues}
          setCustomEvents={setCustomEvents}
          setPhosphoTaskId={setPhosphoTaskId}
        />
      )}
      {aboutYouValues !== null && (
        <AddEvents
          project_id={params.id}
          customEvents={customEvents}
          phosphoTaskId={phosphoTaskId}
          redirectTo={redirectTo}
        />
      )}
    </>
  );
}
