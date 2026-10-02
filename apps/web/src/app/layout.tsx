import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppLayout } from "@/components/layout/AppLayout";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

// Only claims the product can back today: Tanzania (DSE) research, every figure from a cited document.
// icon.png, apple-icon.png, favicon.ico and opengraph-image.png in this folder are picked up by Next.
const DESCRIPTION =
  "African financial intelligence. Research on companies listed on the Dar es Salaam Stock Exchange, with every figure traced to the page of the document it came from.";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  applicationName: "AfriEdge",
  title: {
    default: "AfriEdge | African Financial Intelligence",
    template: "%s | AfriEdge",
  },
  description: DESCRIPTION,
  openGraph: { siteName: "AfriEdge", title: "AfriEdge | African Financial Intelligence", description: DESCRIPTION, type: "website" },
  twitter: { card: "summary_large_image", title: "AfriEdge", description: DESCRIPTION },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
