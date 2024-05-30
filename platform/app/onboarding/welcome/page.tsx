"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { ArrowBigDown, Bot, ThumbsDown, ThumbsUp, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import * as React from "react";

const CARD_STYLE =
  "flex flex-col aspect-square items-left justify-center p-6 text-xl font-semibold space-y-4";

function WhatIsPhospho() {
  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div className="pt-10">Welcome to phospho.</div>
          <div>
            phospho helps you understand your Users' behavior on your LLM app.
          </div>
          <div className="flex justify-center pt-10">
            <ArrowBigDown
              className="w-16 h-16"
              // Add an animation to make it move up and down, slowly
              style={{ animation: "bounce 2s infinite" }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function WhatAreTasks() {
  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div>Your Users interact with an Assistant.</div>
          <div className="pb-4">
            We call "task" every meaningful interaction.
          </div>
          <div className="flex flex-col justify-center text-sm font-normal space-y-2">
            <div className="w-full flex justify-end items-center">
              <div className="rounded-sm bg-blue-600 text-white p-2">
                What's the capital of France?
              </div>
              <User className="w-6 h-6 ml-2 text-primary" />
            </div>
            <div className="w-full flex justify-end items-center text-muted-foreground text-xs italic">
              Task input
            </div>
            <div className="w-full flex justify-start items-center">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className=" p-2 text-muted-foreground">(thinking...)</div>
            </div>
            <div className="w-full flex justify-start items-center">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className=" p-2 text-muted-foreground">
                (intermediate steps...)
              </div>
            </div>
            <div className="w-full flex justify-start items-center">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className="rounded-sm bg-gray-300 p-2 text-gray-800">
                The capital of France is Paris.
              </div>
            </div>
            <div className="w-full flex justify-start items-center text-muted-foreground text-xs italic">
              Task output
            </div>
          </div>
          <div className="flex flex-grow justify-center text-muted-foreground font-normal text-sm italic text-center">
            This a task! It can be anything, not just a question or a
            conversation.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function WhatIsEvaluation() {
  const [thumbs, set_thumbs] = useState<"up" | "down" | null>(null);

  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div>A task is made of an input and an output.</div>

          <div>
            phospho evaluates automatically if this output was{" "}
            <span className="text-green-500">good</span> or{" "}
            <span className="text-red-500">bad</span>.
          </div>
          <div className="flex items-center font-normal text-muted-foreground">
            Improve automatic evaluation by collecting user feedback, using the
            API, and adding labels.
          </div>
          <div className="flex justify-center flex-grow">
            <div className="flex flex-row items-center p-2 space-x-4">
              <HoverCard openDelay={50} closeDelay={50}>
                <HoverCardTrigger>
                  <ThumbsDown
                    className={`w-16 h-16 hover:text-red-500 cursor-pointer rounded-sm p-1
                  ${thumbs === "down" ? "text-white bg-red-500 hover:text-white" : ""}`}
                    onClick={() => {
                      if (thumbs === "down") set_thumbs(null);
                      else set_thumbs("down");
                    }}
                  />
                </HoverCardTrigger>
                <HoverCardContent side="top">Click me!</HoverCardContent>
              </HoverCard>

              <HoverCard openDelay={50} closeDelay={50}>
                <HoverCardTrigger>
                  <ThumbsUp
                    className={`w-16 h-16 hover:text-green-500 cursor-pointer rounded-sm p-1
                  ${thumbs === "up" ? "text-white bg-green-500 hover:text-white" : ""}`}
                    onClick={() => {
                      if (thumbs === "up") set_thumbs(null);
                      else set_thumbs("up");
                    }}
                  />
                </HoverCardTrigger>
                <HoverCardContent side="top">Click me!</HoverCardContent>
              </HoverCard>
            </div>
          </div>
          <div className="flex justify-center flex-grow text-muted-foreground font-normal text-sm italic">
            Add labels to improve automatic evaluation.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function WhatAreSessions() {
  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div>Provide the full context.</div>
          <div className="pb-10">
            Group tasks into sessions and add metadata (eg: system prompt or
            user id)
          </div>

          <div className="flex flex-col justify-center text-sm font-normal space-y-2">
            <div className="w-full flex justify-end items-center">
              <div className="rounded-sm bg-blue-600 text-white p-2 w-32"></div>
              <User className="w-6 h-6 ml-2 text-primary" />
            </div>
            <div className="w-full flex justify-start items-top">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className="rounded-sm bg-gray-300 p-2 text-gray-800 w-32 h-8"></div>
            </div>
            <div className="w-full flex justify-end items-center">
              <div className="rounded-sm bg-blue-600 text-white p-2 w-16"></div>
              <User className="w-6 h-6 ml-2 text-primary" />
            </div>
            <div className="w-full flex justify-start items-center">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className="rounded-sm bg-gray-300 p-2 text-gray-800 w-20 h-4"></div>
            </div>
            <div className="w-full flex justify-end items-top">
              <div className="rounded-sm bg-blue-600 text-white p-2 w-32 h-12"></div>
              <User className="w-6 h-6 ml-2 text-primary" />
            </div>
            <div className="w-full flex justify-start items-center">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className="rounded-sm bg-gray-300 p-2 text-gray-800 w-40 h-4"></div>
            </div>
          </div>
          <div className="flex flex-grow justify-center text-muted-foreground font-normal text-sm italic text-center">
            For example, a conversation is a session.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function WhatAreEvents() {
  const router = useRouter();

  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div className="pt-4">Events are key moments in a session.</div>
          <div>Events are automatically detected.</div>
          <div>They are customizable.</div>
          <div className="flex justify-center pt-6">
            <Button
              onClick={() => router.push("/onboarding/create-project")}
              className="bg-green-500 text-2xl p-10"
              variant="outline"
            >
              Got it. Let's get started!
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function Page() {
  const [carousel_array] = useState([1, 2, 3, 4, 5]);

  return (
    <>
      <div className="flex justify-center pt-10">
        <Carousel
          className="md:w-1/2 max-w-xs"
          orientation="vertical"
          opts={{
            // loop: true,
            // skipSnaps: true,
            // dragFree: true,
            watchDrag: false,
          }}
        >
          <CarouselContent>
            {carousel_array.map((_, index) => (
              <CarouselItem key={index}>
                {index === 0 && <WhatIsPhospho />}{" "}
                {index === 1 && <WhatAreTasks />}{" "}
                {index === 2 && <WhatIsEvaluation />}
                {index === 3 && <WhatAreSessions />}
                {index === 4 && <WhatAreEvents />}
              </CarouselItem>
            ))}
          </CarouselContent>
        </Carousel>
      </div>
    </>
  );
}
