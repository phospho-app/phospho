"use client";

import { redirect } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  redirect(`/org/transcripts/users/${params.id}/tasks`);
}
