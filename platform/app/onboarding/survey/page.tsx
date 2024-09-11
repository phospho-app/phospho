"use client";

import { EventDefinition } from "@/models/models";
import { useState } from "react";

import AboutYou from "./about-you";

export default function Page() {
  const [, setAboutYouValues] = useState(null);
  const [, setCustomEvents] = useState<EventDefinition[] | null>(null);
  const [, setPhosphoTaskId] = useState<string | null>(null);

  // This page is called during onboarding, but also when the users clicks the
  // "Add suggested events" in the dashboard. In the latter case, there is
  // a redirect parameter in the query string. We use it to redirect the user
  // to the correct page after the onboarding is complete.

  return (
    <>
      <AboutYou
        setAboutYouValues={setAboutYouValues}
        setCustomEvents={setCustomEvents}
        setPhosphoTaskId={setPhosphoTaskId}
      />
    </>
  );
}
