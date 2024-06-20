"use client" 

import React, { ReactNode } from 'react'
import { IntercomProvider } from 'react-use-intercom'
import { IntercomWrapper } from './components/intercomWrapper'

export namespace Intercom {
  function getClientId(): string {
    return process.env.NEXT_PUBLIC_INTERCOM_APP_ID || ''
  }

  function isActive(): boolean {
    return !!getClientId()
  }

  export const Provider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const clientId = getClientId()

    if (!isActive()) {
      return children
    }

    return (
      <IntercomProvider appId={clientId}>
        <IntercomWrapper>{children}</IntercomWrapper>
      </IntercomProvider>
    )
  }
}
