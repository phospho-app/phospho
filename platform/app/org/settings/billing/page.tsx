"use client";

import Pricing from "@/components/settings/pricing";
import TaskProgress from "@/components/settings/tasks-quota";
import { UsageGraph } from "@/components/settings/usage-graph";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata, UsageQuota } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ExternalLink } from "lucide-react";
import { useRouter } from "next/navigation";
import useSWR from "swr";

const StripeIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 640 512"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mr-2 w-6 h-6 text-primary"
    >
      <path d="M165 144.7l-43.3 9.2-.2 142.4c0 26.3 19.8 43.3 46.1 43.3 14.6 0 25.3-2.7 31.2-5.9v-33.8c-5.7 2.3-33.7 10.5-33.7-15.7V221h33.7v-37.8h-33.7zm89.1 51.6l-2.7-13.1H213v153.2h44.3V233.3c10.5-13.8 28.2-11.1 33.9-9.3v-40.8c-6-2.1-26.7-6-37.1 13.1zm92.3-72.3l-44.6 9.5v36.2l44.6-9.5zM44.9 228.3c0-6.9 5.8-9.6 15.1-9.7 13.5 0 30.7 4.1 44.2 11.4v-41.8c-14.7-5.8-29.4-8.1-44.1-8.1-36 0-60 18.8-60 50.2 0 49.2 67.5 41.2 67.5 62.4 0 8.2-7.1 10.9-17 10.9-14.7 0-33.7-6.1-48.6-14.2v40c16.5 7.1 33.2 10.1 48.5 10.1 36.9 0 62.3-15.8 62.3-47.8 0-52.9-67.9-43.4-67.9-63.4zM640 261.6c0-45.5-22-81.4-64.2-81.4s-67.9 35.9-67.9 81.1c0 53.5 30.3 78.2 73.5 78.2 21.2 0 37.1-4.8 49.2-11.5v-33.4c-12.1 6.1-26 9.8-43.6 9.8-17.3 0-32.5-6.1-34.5-26.9h86.9c.2-2.3 .6-11.6 .6-15.9zm-87.9-16.8c0-20 12.3-28.4 23.4-28.4 10.9 0 22.5 8.4 22.5 28.4zm-112.9-64.6c-17.4 0-28.6 8.2-34.8 13.9l-2.3-11H363v204.8l44.4-9.4 .1-50.2c6.4 4.7 15.9 11.2 31.4 11.2 31.8 0 60.8-23.2 60.8-79.6 .1-51.6-29.3-79.7-60.5-79.7zm-10.6 122.5c-10.4 0-16.6-3.8-20.9-8.4l-.3-66c4.6-5.1 11-8.8 21.2-8.8 16.2 0 27.4 18.2 27.4 41.4 .1 23.9-10.9 41.8-27.4 41.8zm-126.7 33.7h44.6V183.2h-44.6z" />
    </svg>
  );
};

export default function Page() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const { accessToken, loading } = useUser();
  const toast = useToast();
  const router = useRouter();

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const plan = selectedOrgMetadata?.plan;

  const { data: billingPortalLink } = useSWR(
    [`/api/organizations/${selectedOrgId}/billing-portal`, accessToken],
    ([url, token]) =>
      authFetcher(url, token, "POST").then((res) => res.portal_url),
    {
      keepPreviousData: true,
    },
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

  const { data: usage }: { data: UsageQuota | null | undefined } = useSWR(
    [`/api/organizations/${selectedOrgId}/usage-quota`, accessToken],
    ([url, token]) => authFetcher(url, token),
    {
      keepPreviousData: true,
    },
  );

  const currentUsage = usage?.current_usage;
  const maxUsage = usage?.max_usage;
  // format next_invoice_total to dollars
  const nextInvoiceTotal =
    usage?.next_invoice_total !== undefined &&
    usage?.next_invoice_total !== null
      ? `$${usage.next_invoice_total / 100}`
      : "...";

  // TODO : Add somewhere the next invoice amount due

  if (loading) {
    return <>Loading...</>;
  }

  return (
    <>
      <h2 className="text-2xl font-bold tracking-tight mb-4">Billing</h2>
      <div className="space-y-4 mb-8">
        {plan === "pro" && (
          // TODO: Display usage for pro plan in number of logs
          <></>
        )}
        {plan === "usage_based" && (
          <p>
            Your usage so far this month has a total cost of: {nextInvoiceTotal}
          </p>
        )}
        {plan === "hobby" && (
          <>
            <h2 className="text-2xl font-bold tracking-tight">Usage</h2>
            <TaskProgress
              currentValue={currentUsage ?? 0}
              maxValue={maxUsage ?? 1}
            />
            <p>
              You have currently run {currentUsage ?? "..."}/{maxUsage} free
              analysis.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Add a payment method to increase limit.
            </p>
          </>
        )}
        {usage && usage.balance_transaction < 0 && (
          <p>
            🎁 You received {-usage.balance_transaction / 100}$ of free credits.
            They will be applied to the next invoice.
          </p>
        )}
        <div>
          You plan is: <code className="bg-secondary p-1.5">{plan}</code>
        </div>
        {plan && plan !== "hobby" && plan !== "self-hosted" && (
          <div className="flex flex-col space-y-1 items-start">
            <Button variant="secondary" onClick={onBillingPortalClick}>
              <StripeIcon />
              Manage billing
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </div>
        )}
      </div>
      <div>
        <UsageGraph />
      </div>
      <div className="space-y-2 mb-8 pt-8">
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
      </div>
    </>
  );
}
