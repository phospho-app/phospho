"use client";

import { useUser } from "@propelauth/nextjs/client";
import { useEffect } from "react";

interface IntercomSettings {
  api_base: string;
  app_id: string | undefined;
  user_id?: string;
  email?: string;
}

type IntercomCommand =
  | "reattach_activator"
  | "update"
  | "hide"
  | "show"
  | "showNewMessage"
  | string; // For any other commands

interface IntercomFunc {
  (command: IntercomCommand, settings?: IntercomSettings): void;
  (command: "boot", settings: IntercomSettings): void;
}
declare global {
  interface Window {
    intercomSettings: IntercomSettings;
    Intercom: IntercomFunc;
  }
}

const IntercomClientComponent: React.FC = () => {
  const { user } = useUser();
  useEffect(() => {
    let app_id: string | undefined = undefined;
    try {
      app_id = `${process.env.NEXT_PUBLIC_INTERCOM_APP_ID}`;
    } catch (e) {
      console.error(e);
    }
    window.intercomSettings = {
      api_base: "https://api-iam.intercom.io",
      // Replace with your Intercom app ID.
      app_id: app_id,
    };

    if (user) {
      window.intercomSettings.user_id = user.userId;
      window.intercomSettings.email = user.email;
    }

    if (window.Intercom) {
      window.Intercom("reattach_activator");
      window.Intercom("update", window.intercomSettings);
    } else {
      const intercomScript = document.createElement("script");
      intercomScript.type = "text/javascript";
      intercomScript.async = true;
      intercomScript.src = `https://widget.intercom.io/widget/${process.env.NEXT_PUBLIC_INTERCOM_APP_ID}`; // Ensure this matches your Intercom app ID.
      intercomScript.onload = () =>
        window.Intercom("update", window.intercomSettings);
      document.body.appendChild(intercomScript);
    }
  }, [user]);
  return null; // This component does not render anything visually.
};
export default IntercomClientComponent;
