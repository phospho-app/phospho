"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import { ArrowBigDown, Bot, User } from "lucide-react";
import Link from "next/link";
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
            phospho helps you understand your Users&apos; behavior on your LLM
            app.
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
          <div className="flex flex-col justify-center text-sm font-normal space-y-2">
            <div className="w-full flex justify-end items-center">
              <div className="rounded-sm bg-blue-600 text-white p-2">
                What&apos;s the capital of France?
              </div>
              <User className="w-6 h-6 ml-2 text-primary" />
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
          <div className="pb-10">
            Messages are grouped using <code>session_id</code>,{" "}
            <code>user_id</code>, and <code>version_id</code>.
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
            A conversation is a session.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function WhatAreEvents() {
  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div>phospho runs analytics to augment your data.</div>
          <div>Easily customize them on the platform.</div>
          <div className="flex flex-col justify-center text-sm font-normal space-y-2 ">
            <div className="flex justify-end items-center">
              <div className="rounded-sm bg-blue-600 text-white p-2 w-32"></div>
              <User className="w-6 h-6 ml-2 text-primary" />
            </div>
            <div className="flex justify-start items-top">
              <Bot className="w-6 h-6 mr-2 text-primary" />
              <div className="rounded-sm bg-gray-300 p-2 text-gray-800 w-32 h-8"></div>
            </div>
            <div className="flex justify-center">
              <ArrowBigDown className="w-6 h-6" />
            </div>
            <div className="flex flex-col space-y-2">
              <div className="rounded-lg border-muted-foreground border-2 p-1">
                Tag: Vague question
              </div>
              <div className="rounded-lg border-muted-foreground border-2 p-1">
                Score: Conciseness 1/5
              </div>
              <div className="rounded-lg border-muted-foreground border-2 p-1">
                Category: Product feedback
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function LetsGo() {
  const router = useRouter();

  return (
    <div className="p-1">
      <Card>
        <CardContent className={CARD_STYLE}>
          <div className="pt-4">
            Learn more in the{" "}
            <Link
              href="https://phospho-app.github.io/docs/welcome"
              target="_blank"
              className="underline"
            >
              docs
            </Link>
            .
          </div>
          <div className="flex justify-center pt-6">
            <Button
              onClick={() => router.push("/onboarding/survey")}
              className="bg-green-500 text-2xl p-10"
              variant="outline"
            >
              Got it. Let&apos;s get started!
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
                {index === 2 && <WhatAreSessions />}
                {index === 3 && <WhatAreEvents />}
                {index === 4 && <LetsGo />}
              </CarouselItem>
            ))}
          </CarouselContent>
        </Carousel>
      </div>
    </>
  );
}
