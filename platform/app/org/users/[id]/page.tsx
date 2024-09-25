"use client";

import { redirect } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const user_id = params.id;

  if (user_id) {
    redirect(`/org/transcripts/users/${user_id}`);
  } else {
    redirect("/org/transcripts/users");
  }
}
