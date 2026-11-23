import type {Metadata} from "next";
import "@fontsource/barlow/400.css";
import "@fontsource/barlow/500.css";
import "@fontsource/barlow/600.css";
import "@fontsource/barlow-condensed/500.css";
import "@fontsource/barlow-condensed/600.css";
import "./globals.css";
import {Shell} from "@/components/Shell";

export const metadata: Metadata = {
  title: "Battery Passport 360",
  description: "Independent prototype: synthetic industrial battery fleet health, passport evidence readiness and measured cell research.",
  robots: {index: false, follow: false},  // demo link: keep out of search engines
};

export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><Shell>{children}</Shell></body></html>;
}
