"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";

export function SelectOrgButton() {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  // PropelAuth
  const { user } = useUser();

  if (user === undefined || user === null) return;
  if (user.orgIdToOrgMemberInfo === undefined) return;
  if (selectedOrgId === undefined) return;

  const orgsArray = Object.values(user.orgIdToOrgMemberInfo);

  const handleValueChange = (newOrgId: string) => {
    setproject_id(null);
    setSelectedOrgId(newOrgId);
  };

  if (!selectedOrgId) {
    return <></>;
  }

  return (
    <div className="px-3 py-2 sm:max-w-1/4">
      <Select onValueChange={handleValueChange}>
        <SelectTrigger>
          <SelectValue asChild={true}>
            <div>
              {user.orgIdToOrgMemberInfo[selectedOrgId]?.orgName ||
                "Select an Organization"}
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent
          position="popper"
          className="overflow-y-auto max-h-[20rem]"
        >
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
