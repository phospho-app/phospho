"use client";

import { SelectOrgButton } from "@/components/settings/select-org-dropdown";
import { CenteredSpinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import UpgradeButton from "@/components/upgrade-button";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useRedirectFunctions, useUser } from "@propelauth/nextjs/client";
import { CopyIcon } from "lucide-react";
import Link from "next/link";

export default function Page() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  const { redirectToAccountPage, redirectToOrgPage } = useRedirectFunctions();
  const { loading, user } = useUser();

  const plan = selectedOrgMetadata?.plan ?? "hobby";

  if (loading) {
    return <CenteredSpinner />;
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold tracking-tight mb-4">Your Account</h2>
        <p>Currently logged in user: {user?.email}</p>
        <div className="mt-4 mb-4">
          <Button variant="secondary" onClick={redirectToAccountPage}>
            Manage Account
          </Button>
        </div>
      </div>
      <h2 className="text-2xl font-bold tracking-tight mb-4">Organization</h2>

      <div className="space-x-2">
        <div>
          Selected organization:
          <SelectOrgButton />
        </div>
        <div className="md:flex flex-auto items-center my-2">
          <p>Your organization id: {selectedOrgId}</p>
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              if (selectedOrgId) {
                navigator.clipboard.writeText(selectedOrgId);
              }
            }}
          >
            <CopyIcon size="16" />
          </Button>
        </div>
        <Link
          href={`${process.env.NEXT_PUBLIC_AUTH_URL}/org/api_keys/${selectedOrgId}`}
        >
          <Button variant="secondary">Get API keys</Button>
        </Link>
        <Button
          variant="secondary"
          onClick={() => redirectToOrgPage(selectedOrgId ?? undefined)}
        >
          Invite collaborators
        </Button>
        {plan === "hobby" && (
          <>
            <UpgradeButton />
            <div className="mt-4">
              <div>
                <Link href="/org/settings/billing" className="underline">
                  Add a payment method
                </Link>{" "}
                to invite more members to your organization.
              </div>
            </div>
          </>
        )}
        {plan === "pro" && (
          <div>You can invite up to 15 collaborators per organization.</div>
        )}
      </div>
    </div>
  );
}
