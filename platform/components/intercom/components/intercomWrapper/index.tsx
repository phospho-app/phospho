"use client"

import React, { ReactNode, useEffect } from 'react'
import { useIntercom } from 'react-use-intercom'
import { useUser } from "@propelauth/nextjs/client";

export const IntercomWrapper: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { boot, update, shutdown } = useIntercom()
  const { user } = useUser();

  useEffect(() => {
    if (user) {
      boot({
        // name: user?.name,
        email: user.email,
        customAttributes: {
          // credits: coreStore.organization?.credits,
          // projects: coreStore.projects?.length || 0,
        },
      })
    } else {
      shutdown()
    }
  }, [user])

  return <>{children}</>
}
