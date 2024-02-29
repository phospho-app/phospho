"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import Image from "next/image";

import "../globals.css";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <FetchOrgProject />
      <div>
        {/* <Image
          src="/image/green-galaxy.jpg"
          //   fill={true}
          // layout="fill"
          quality={100}
          width={1920}
          height={1080}
          alt="background image of a green galaxy"
          style={{
            objectFit: "fill",
            zIndex: -10,
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            overflow: "hidden",
          }}
        /> */}
      </div>
      <section>
        <div className="flex flex-row justify-between items-bottom p-8">
          <div>
            <h2
              className="text-3xl font-semibold text-green-500 pt-0"
              style={{
                position: "fixed",
              }}
            >
              phospho
            </h2>
          </div>
        </div>
        <div className="max-w-screen overflow-hidden ">
          {/* <div className="flex flex-col align-middle"> */}
          <div className="flex flex-col items-center justify-center p-4">
            {children}
          </div>
        </div>
      </section>
    </>
  );
}
