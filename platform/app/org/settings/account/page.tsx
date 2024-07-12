"use client";

import { CenteredSpinner } from "@/components/SmallSpinner";
import { SelectOrgButton } from "@/components/settings/SelectOrgDropdown";
import { Button } from "@/components/ui/Button";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useRedirectFunctions, useUser } from "@propelauth/nextjs/client";
import { CircleUser, CopyIcon, ExternalLink, UserPlus } from "lucide-react";
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
    <>
      <div className="mb-8 space-y-2">
        <h2 className="text-2xl font-bold tracking-tight mb-4">Your Account</h2>
        <p>
          Currently logged in user:{" "}
          <code className="bg-secondary p-1.5">{user?.email}</code>
        </p>
        <div>
          <Button
            variant="secondary"
            onClick={() => {
              redirectToAccountPage({
                redirectBackToUrl: window.location.hostname,
              });
            }}
          >
            <CircleUser className="w-4 h-4 mr-2" />
            Manage Account <ExternalLink className="w-3 h-3 ml-2" />
          </Button>
        </div>
      </div>
      <div className="mb-8 space-y-2">
        <h2 className="text-2xl font-bold tracking-tight mb-1">Organization</h2>
        <div className="text-sm text-muted-foreground mb-4">
          Organizations are used to share projects and manage billing.
        </div>
        <div className="space-y-2 pb-4">
          <div className="md:flex flex-auto items-center">
            <p>
              Organization id:{" "}
              <code className="bg-secondary p-1.5">{selectedOrgId}</code>
            </p>
            <Button
              variant="outline"
              className="ml-2"
              size="icon"
              onClick={() => {
                if (selectedOrgId) {
                  navigator.clipboard.writeText(selectedOrgId);
                }
              }}
            >
              <CopyIcon className="w-3 h-3" />
            </Button>
          </div>
        </div>
        <div className="space-y-2 pb-4">
          <h2 className="text-xl font-bold tracking-tight">Invite</h2>
          <div className="text-sm text-muted-foreground">
            Share your projects by inviting them to join your organization.
          </div>
          <Button
            variant="secondary"
            onClick={() => redirectToOrgPage(selectedOrgId ?? undefined)}
            disabled={plan === "hobby"}
          >
            <UserPlus className="w-4 h-4 mr-2" />
            Invite to organization <ExternalLink className="w-3 h-3 ml-2" />
          </Button>
          {plan === "hobby" && (
            <div className="text-sm text-muted-foreground">
              <Link href="/org/settings/billing" className="underline">
                Add a payment method
              </Link>{" "}
              to invite more members.
            </div>
          )}
          {plan === "pro" && (
            <div className="text-sm text-muted-foreground">
              You can invite up to 15 members per organization.
            </div>
          )}
        </div>
      </div>
      <div className="space-y-2 pb-4">
        <h2 className="text-xl font-bold tracking-tight">Switch</h2>
        <div className="text-sm text-muted-foreground">
          Your account can belong to multiple organizations. Switch between them
          here.
        </div>
        <SelectOrgButton />
      </div>
      {plan === "self-hosted" && (
        <div className="mb-8 space-y-2">
          <h2 className="text-2xl font-bold tracking-tight mb-4">
            Self-hosted
          </h2>
          <div className="mt-4">You are in self-hosted mode</div>
        </div>
      )}
    </>
  );
}
