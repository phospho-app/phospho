"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";

interface OrgMemberInfo {
  orgId: string;
  orgName: string;
}

export function SelectOrgButton() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  // PropelAuth
  const { user, loading, accessToken } = useUser();

  if (user === undefined || user === null) return;
  if (user.orgIdToOrgMemberInfo === undefined) return;
  if (selectedOrgId === undefined) return;

  const orgsArray = Object.values(user.orgIdToOrgMemberInfo);

  const handleValueChange = (selectedOrgId: string) => {
    setSelectedOrgId(selectedOrgId);
    setproject_id(null);
    // Additional logic here if needed
  };

  if (!selectedOrgId) {
    return <></>;
  }

  return (
    <div className="px-3 py-2">
      <Select onValueChange={handleValueChange}>
        <SelectTrigger>
          <SelectValue asChild={true}>
            <div>
              {user.orgIdToOrgMemberInfo[selectedOrgId]?.orgName ||
                "Select an Organization"}
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent position="popper">
          {orgsArray.map((org) => (
            <SelectItem key={org.orgId} value={org.orgId}>
              {org.orgName}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
