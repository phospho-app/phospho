"use client";

import { redirect } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  redirect(`/org/users/${params.id}/tasks`);
}
