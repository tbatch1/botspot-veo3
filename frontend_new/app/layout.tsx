import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "OTT Ad Builder",
    description: "AI-Powered Video Ad Creation",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" className="dark" suppressHydrationWarning>
            <body className={cn(inter.className, "bg-slate-950 text-slate-50 min-h-screen")} suppressHydrationWarning>
                <div className="fixed inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
                <main className="relative z-10 w-full h-full">
                    {children}
                </main>
            </body>
        </html>
    );
}
