"use client";

import { SessionsTable } from "@/components/sessions/sessions-table";

const User = ({ params }: { params: { user_id: string } }) => {
  const user_id = decodeURIComponent(params.user_id);

  return (
    <>
      <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
        <SessionsTable forcedDataFilters={{ user_id: user_id }} />
      </div>
    </>
  );
};

export default User;
