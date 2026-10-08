import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";
import { AppLayout } from "@/components/layout/AppLayout";

// IBM Plex: a sober, highly legible family with true tabular figures, made for dense numbers and tables.
const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500"] });

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

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f6f6f4" },
    { media: "(prefers-color-scheme: dark)", color: "#0d0e10" },
  ],
};

// Runs while the HTML is parsed, before the first paint, so a saved dark theme never flashes light
// (node_modules/next/dist/docs/01-app/02-guides/preventing-flash-before-hydration.md). A fixed string:
// nothing from a request or a user is interpolated into it.
const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem("afriedge-theme");if(t!=="light"&&t!=="dark"){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" data-theme="light" suppressHydrationWarning className={`${plexSans.variable} ${plexMono.variable} h-full antialiased`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col font-sans">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
