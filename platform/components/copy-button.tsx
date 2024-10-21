"use client";

import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { cn } from "@/lib/utils";
import { Check, Copy } from "lucide-react";
import { useState } from "react";

export interface useCopyToClipboardProps {
  timeout?: number;
}

export function useCopyToClipboard({
  timeout = 2000,
}: useCopyToClipboardProps) {
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const copyToClipboard = (value: string) => {
    if (typeof window === "undefined" || !navigator.clipboard?.writeText) {
      return;
    }

    if (!value) {
      return;
    }

    navigator.clipboard.writeText(value).then(() => {
      setIsCopied(true);

      setTimeout(() => {
        setIsCopied(false);
      }, timeout);
    });
  };

  return { isCopied, copyToClipboard };
}

export type CopyButtonProps = {
  text: string;
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link"
    | null
    | undefined;
  size?: "default" | "sm" | "lg" | "icon" | null | undefined;
  className?: string;
};

export function CopyButton({
  text,
  variant,
  size,
  className,
}: CopyButtonProps) {
  const { isCopied, copyToClipboard } = useCopyToClipboard({ timeout: 2000 });

  const onCopy = () => {
    if (isCopied) return;
    copyToClipboard(text);
  };

  return (
    <HoverCard openDelay={80} closeDelay={30}>
      <HoverCardTrigger>
        <Button
          variant={variant ? variant : "outline"}
          size={size ? size : "icon"}
          className={cn(className, "text-xs size-4")}
          onClick={onCopy}
        >
          {isCopied ? (
            <Check className="w-3 h-3" />
          ) : (
            <Copy className="w-3 h-3" />
          )}
        </Button>
      </HoverCardTrigger>
      <HoverCardContent side="bottom" className="text-sm text-center ml-2">
        {isCopied ? "Copied!" : "Copy"}
      </HoverCardContent>
    </HoverCard>
  );
}
