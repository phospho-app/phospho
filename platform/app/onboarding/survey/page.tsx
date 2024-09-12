"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import { useState } from "react";

import AboutYou from "./about-you";
import { AboutYouFormValues } from "./about-you";

export default function Page() {
  const [, setAboutYouValues] = useState<AboutYouFormValues | null>(null);

  // This page is called during onboarding, but also when the users clicks the
  // "Add suggested events" in the dashboard. In the latter case, there is
  // a redirect parameter in the query string. We use it to redirect the user
  // to the correct page after the onboarding is complete.

  return (
    <>
      <FetchOrgProject />
      <AboutYou setAboutYouValues={setAboutYouValues} />
    </>
  );
}
