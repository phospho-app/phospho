"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import React from 'react';
import Intercom from '@intercom/messenger-js-sdk';

import AddEvents from "./add-events";

export default function Page({ params }: { params: { id: string } }) {
  const [phosphoTaskId] = useState<string | null>(null);

  // This page is called during onboarding, but also when the users clicks the
  // "Add suggested events" in the dashboard. In the latter case, there is
  // a redirect parameter in the query string. We use it to redirect the user
  // to the correct page after the onboarding is complete.
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");
  const redirectTo = redirect == "events" ? "/org/insights/events" : "/org";

  Intercom({
    app_id: process.env.NEXT_PUBLIC_INTERCOM_APP_ID || '',
  });

  return (
    <>
      <AddEvents
        project_id={params.id}
        phosphoTaskId={phosphoTaskId}
        redirectTo={redirectTo}
      />
    </>
  );
}
