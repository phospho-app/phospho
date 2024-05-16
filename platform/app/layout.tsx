import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";
// PropelAuth
import { AuthProvider } from "@propelauth/nextjs/client";
import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { Inter } from "next/font/google";

import "./globals.css";
// PostHog
import { PHProvider } from "./providers";

const PostHogPageView = dynamic(() => import("./PostHogPageView"), {
  ssr: false,
});

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "phospho",
  description: "The LLM analytics platform",
  metadataBase: new URL("https://phospho.app/"),
  twitter: {
    card: "summary_large_image",
    title: "phospho",
    description: "The LLM analytics platform",
    creator: "@phospho_app",
    images: ["https://phospho.app/image/twitterpreview.png"],
  },
  openGraph: {
    type: "website",
    title: "phospho",
    description: "The LLM analytics platform",
    images: [
      {
        url: "https://phospho.app/image/opengraph-image.png",
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
          </body>
        </AuthProvider>
      </PHProvider>
    </html>
  );
}
