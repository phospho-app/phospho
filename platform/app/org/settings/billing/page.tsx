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

  const plan = selectedOrgMetadata?.plan;

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

  if (loading) {
    return <>Loading...</>;
  }

  return (
    <>
      <div className="flex flex-col space-y-2">
        {plan && plan !== "hobby" && plan !== "self-hosted" && (
          <Button
            variant="secondary"
            onClick={onBillingPortalClick}
            className="w-80"
          >
            Manage subscription
          </Button>
        )}
        {plan === "hobby" && (
          <Pricing
            currentPlan={null}
            selectedPlan="usage_based"
            proPlanTagline="Add payment method"
            displayHobbyCTA={true}
          />
        )}
        {plan === "usage_based" && <Pricing currentPlan="usage_based" />}
        {plan === "pro" && <Pricing currentPlan="pro" />}
        {plan === "self-hosted" && <Pricing currentPlan="self-hosted" />}
        <div className="h-20"></div>
      </div>
    </>
  );
}
