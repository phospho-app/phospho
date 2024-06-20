"use client";

import ABTesting from "@/components/abtesting/abtesting";
import React from 'react';
import Intercom from '@intercom/messenger-js-sdk';

export default function Page() {
  Intercom({
    app_id: process.env.NEXT_PUBLIC_INTERCOM_APP_ID || '',
  });
  return <ABTesting />;
}
