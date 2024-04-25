"use client";

import { Button } from "@/components/ui/button";
import { useRedirectFunctions } from "@propelauth/nextjs/client";
import React from "react";

const Authenticate: React.FC = () => {
  const { redirectToSignupPage, redirectToLoginPage } = useRedirectFunctions();
  return (
    <>
      <div className="hidden"></div>
      <div className="h-screen container relative h-[800px] flex-col items-center justify-center md:grid lg:max-w-none lg:grid-cols-2 lg:px-0 lg:mx-0">
        {/*<Link
              href="/dashboard"
              className={cn(
                buttonVariants({ variant: "ghost" }),
                "absolute right-4 top-4 md:right-8 md:top-8"
              )}
            >
              Login
              </Link>*/}
        <div className="relative hidden h-full flex-col bg-muted p-10 lg:border-r lg:flex">
          <div className="absolute inset-0 bg-gradient-to-r from from-transparent to-green-500" />
          <div className="relative z-20 flex items-center text-lg font-medium">
            phospho
          </div>
          <div className="relative z-20 mt-auto">
            <blockquote className="space-y-2">
              <p className="text-lg">Open source text analytics for LLM apps</p>
              <footer className="text-sm">
                Test, evaluate, guardrail and improve your LLM app
              </footer>
            </blockquote>
          </div>
        </div>
        <div className="lg:p-8">
          <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px] mt-24">
            <div className="flex flex-col space-y-2 text-center">
              <h1 className="text-2xl font-semibold tracking-tight text-green-500">
                Let's get started with phospho.
              </h1>
              <Button
                onClick={() => redirectToSignupPage()}
                className="bg-green-500 text-white hover:bg-gray-50 hover:text-green-500 hover:border hover:border-green-500"
              >
                Sign up
              </Button>
              <Button variant="secondary" onClick={() => redirectToLoginPage()}>
                Login
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Authenticate;
