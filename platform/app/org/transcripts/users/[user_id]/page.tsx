"use client";

import { redirect } from "next/navigation";

export default function Page({ params }: { params: { user_id: string } }) {
  redirect(`/org/transcripts/users/${params.user_id}/messages`);
}
