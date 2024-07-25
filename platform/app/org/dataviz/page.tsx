"use client";

import { redirect } from "next/navigation";

// The historical dashboard was removed. We redirect to the tasks page, which is
// the new default page.

export default function Page() {
  redirect("/org/dataviz/dashboard");
}
