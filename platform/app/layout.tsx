// Intercom
import IntercomClientComponent from "@/components/IntercomClientComponent";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Toaster } from "@/components/ui/Toaster";
// PropelAuth
import { AuthProvider } from "@propelauth/nextjs/client";
import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { Inter } from "next/font/google";
import Script from "next/script";

import "./globals.css";
// PostHog
import { PHProvider } from "./providers";

const PostHogPageView = dynamic(() => import("./PostHogPageView"), {
  ssr: false,
});

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "phospho AI",
  description: "The LLM analytics platform that helps you understand your data",
  metadataBase: new URL("https://platform.phospho.ai"),
  twitter: {
    card: "summary_large_image",
    title: "phospho AI",
    description:
      "The LLM analytics platform that helps you understand your data",
    creator: "@phospho_app",
    images: ["https://platform.phospho.ai/image/twitterpreview.png"],
  },
  openGraph: {
    type: "website",
    title: "phospho AI",
    description:
      "The LLM analytics platform that helps you understand your data",
    images: [
      {
        url: "https://platform.phospho.ai/image/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "phospho",
      },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <meta property="og:image" content="<generated>" />
      <meta property="og:image:type" content="<generated>" />
      <meta property="og:image:width" content="<generated>" />
      <meta property="og:image:height" content="<generated>" />
      <meta name="twitter:image" content="<generated>" />
      <meta name="twitter:image:type" content="<generated>" />
      <meta name="twitter:image:width" content="<generated>" />
      <meta name="twitter:image:height" content="<generated>" />
      <PHProvider>
        <AuthProvider authUrl={process.env.NEXT_PUBLIC_AUTH_URL as string}>
          <body className={inter.className}>
            <PostHogPageView />
            <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
              {children}
              <Toaster />
            </ThemeProvider>
            <Script
              strategy="afterInteractive"
              id="intercom-settings"
              dangerouslySetInnerHTML={{
                __html: `
                        window.intercomSettings = {
                            api_base: "https://api-iam.intercom.io",
                            app_id: ${process.env.NEXT_PUBLIC_INTERCOM_APP_ID}, // Ensure this matches your actual Intercom app ID.
                        };
                    `,
              }}
            />
            <IntercomClientComponent />
          </body>
        </AuthProvider>
      </PHProvider>
    </html>
  );
}
