"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import {
  Carousel,
  CarouselApi,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { ArrowBigDown, ThumbsDown, ThumbsUp } from "lucide-react";
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
            phospho helps you understand your Users behaviour on your LLM app.
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
          <div>We call "task" every meaningful interaction.</div>
          <div className="font-normal text-gray-500">
            An interaction is meaningful if your user can{" "}
            <span className="italic">notice</span> it.
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
            phospho evaluates automatically if this output was good or bad.
          </div>
          <div className="flex items-center font-normal text-gray-500">
            You control this by giving examples to phospho. Label tasks, collect
            user feedback, do your thing...
          </div>
          <div className="flex justify-center flex-grow">
            <div>
              <div className="flex flex-row items-center p-2 space-x-4">
                <ThumbsDown
                  className={`w-16 h-16 hover:text-red-500 cursor-pointer rounded-sm p-1
                  ${thumbs === "down" ? "text-white bg-red-500 hover:text-white" : ""}`}
                  onClick={() => set_thumbs("down")}
                />
                <ThumbsUp
                  className={`w-16 h-16 hover:text-green-500 cursor-pointer rounded-sm p-1
                  ${thumbs === "up" ? "text-white bg-green-500 hover:text-white" : ""}`}
                  onClick={() => set_thumbs("up")}
                />
              </div>
              <div className="text-gray-500 font-normal text-sm italic">
                Click on the thumbs!
              </div>
            </div>
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
          <div>Context matters.</div>
          <div>
            Provide full context by grouping tasks into sessions and adding
            metadata.
          </div>
          <div className="flex items-center font-normal text-gray-500">
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
              // className="bg-green-500 text-2xl p-10 logo-animation"
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
  const [carousel_array, set_carousel_array] = useState([1, 2, 3, 4, 5]);

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
