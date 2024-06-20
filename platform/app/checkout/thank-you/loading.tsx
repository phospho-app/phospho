import { CenteredSpinner } from "@/components/small-spinner";
import React from 'react';
import Intercom from '@intercom/messenger-js-sdk';

export default function Loading() {
  Intercom({
    app_id: process.env.NEXT_PUBLIC_INTERCOM_APP_ID || '',
  });

  return <CenteredSpinner />;
}
