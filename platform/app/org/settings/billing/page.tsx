"use client";

import Pricing from "@/components/settings/pricing";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import useSWR from "swr";

export default function Page() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  const { accessToken, loading } = useUser();
  const toast = useToast();
  const router = useRouter();

  const plan = selectedOrgMetadata?.plan ?? "hobby";

  const { data: billingPortalLink } = useSWR(
    [`/api/organizations/${selectedOrgId}/billing-portal`, accessToken],
    ([url, token]) =>
      authFetcher(url, token, "POST").then((res) => res.portal_url),
  );

  const onBillingPortalClick = async () => {
    if (billingPortalLink) {
      router.push(billingPortalLink);
    } else {
      toast.toast({
        title: "Error",
        description: "Could not find billing portal link. Contact us for help.",
      });
    }
  };

  return (
    <>
      <div className="flex-col">
        <div className="mb-4">
          {plan === "hobby" && (
            <Pricing
              currentPlan={null}
              selectedPlan="pro"
              proPlanTagline="Add payment method"
              displayHobbyCTA={true}
            />
          )}
          {plan === "pro" && <Pricing currentPlan="pro" />}
          {plan && plan !== "hobby" && (
            <Button variant="secondary" onClick={onBillingPortalClick}>
              Manage subscription
            </Button>
          )}
        </div>
      </div>
    </>
  );
}
