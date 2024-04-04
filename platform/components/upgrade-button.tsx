import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { usePostHog } from "posthog-js/react";
import React from "react";

import { useToast } from "./ui/use-toast";

const UpgradeButton = ({
  tagline,
  enlarge,
  green,
}: {
  tagline?: string;
  enlarge?: boolean;
  green?: boolean;
}) => {
  /*
  This is the buy button. It is used to upgrade the user's plan.
  It redirects the user to the Stripe Checkout page.
  */
  if (!tagline) {
    tagline = "Upgrade plan";
  }
  if (enlarge === undefined) {
    enlarge = true;
  }
  if (green === undefined) {
    green = true;
  }

  //posthog
  const posthog = usePostHog();
  // PropelAuth
  const { user, loading, accessToken } = useUser();
  const router = useRouter();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const toast = useToast();

  // const stripeUrl = useMemo(() => {
  //   const stripe_test_url =
  //     "https://billing.phospho.ai/b/test_dR6aG0eT5exi448dQQ";
  //   const stripe_prod_url = "https://billing.phospho.ai/b/cN23fLcyh98kbDObII";

  //   return process.env.NEXT_PUBLIC_APP_ENV === "production"
  //     ? stripe_prod_url
  //     : stripe_test_url;
  // }, []);

  const upgradeButtonClick = async () => {
    try {
      posthog.capture("upgrade_click", {
        propelauthUserId: user?.userId,
      });
      // Call the backend to create a checkout session
      const response = await fetch(
        `/api/organizations/${selectedOrgId}/create-checkout`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        },
      );
      if (!response.ok) {
        console.log("Error: ", response);
        toast.toast({
          title: "Checkout Error - Please try again later",
          description: `Details: ${response.status} - ${response.statusText}`,
        });
        return;
      }
      const data = await response.json();
      if (data?.error) {
        toast.toast({
          title: "Checkout Error - Please try again later",

          description: data?.error || "Error creating checkout session",
        });
        return;
      }
      const stripeUrl = data?.checkout_url;
      if (stripeUrl) {
        router.push(stripeUrl);
      } else {
        toast.toast({
          title: "Checkout Error - Please try again later",
          description: "Error creating checkout session - no stripe url",
        });
      }
    } catch (error) {
      console.log("Error: ", error);
      toast.toast({
        title: "Checkout Error - Please try again later",
        description: "Error creating checkout session: " + error,
      });
    }
  };

  let buttonClass = cn();
  if (enlarge) {
    buttonClass += " text-base";
  }
  if (green) {
    buttonClass += " bg-green-500 hover:bg-green-400";
  }

  return (
    <Button
      variant="default"
      // className="bg-green-500 hover:bg-green-400 text-base"
      className={buttonClass}
      onClick={upgradeButtonClick}
    >
      {tagline}
    </Button>
  );
};

export default UpgradeButton;
