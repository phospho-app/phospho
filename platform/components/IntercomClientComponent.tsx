'use client';
import { useEffect } from "react";
import { useUser } from "@propelauth/nextjs/client";

declare global {
    interface Window {
      intercomSettings: any;
      Intercom: any;
    }
  }

const IntercomClientComponent: React.FC = () => {
    const { user, loading} = useUser();
    useEffect(() => {
        window.intercomSettings = {
            api_base: "https://api-iam.intercom.io",
            app_id: process.env.NEXT_PUBLIC_INTERCOM_APP_ID // Replace with your Intercom app ID.
        };

        if (user) {
            console.log("User is logged in");
            console.log("User :", user);
            window.intercomSettings.user_id = user.userId;
            window.intercomSettings.email = user.email;
        }
        else {
            console.log("User is not logged in");
        }
        console.log("Intercom Settings: ", window.intercomSettings);
        if (window.Intercom) {
            window.Intercom('reattach_activator');
            window.Intercom('update', window.intercomSettings);
        } else {
            const intercomScript = document.createElement('script');
            intercomScript.type = 'text/javascript';
            intercomScript.async = true;
            intercomScript.src = `https://widget.intercom.io/widget/${process.env.NEXT_PUBLIC_INTERCOM_APP_ID}`; // Ensure this matches your Intercom app ID.
            intercomScript.onload = () => window.Intercom('update', window.intercomSettings);
            document.body.appendChild(intercomScript);
        }
    }, [user]);
    return null; // This component does not render anything visually.
};
export default IntercomClientComponent;