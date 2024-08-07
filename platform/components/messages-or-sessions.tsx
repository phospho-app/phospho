"use client";

import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { BriefcaseBusiness } from "lucide-react";
import useSWR from "swr";

import { Button } from "@/components/ui/button";

export function MessagesOrSessions({
    className,
}: React.HTMLAttributes<HTMLDivElement>) {
    const { accessToken } = useUser();
    const project_id = navigationStateStore((state) => state.project_id);
    const messagesOrSessions = navigationStateStore((state) => state.messagesOrSessions);
    const setMessagesOrSessions = navigationStateStore((state) => state.setMessagesOrSessions);

    const handleValueChange = (messageOrSession: "messages" | "sessions") => {
        setMessagesOrSessions(messageOrSession);
    };

    return (
        <Select
            onValueChange={handleValueChange}
            defaultValue={messagesOrSessions}
        >
            <SelectTrigger>
                {messagesOrSessions === "messages" ? "Messages" : "Sessions"}
            </SelectTrigger>
            <SelectContent>
                <SelectGroup>
                    <SelectItem value="messages">Messages</SelectItem>
                    <SelectItem value="sessions">Sessions</SelectItem>
                </SelectGroup>
            </SelectContent>
        </Select>
    );
}
