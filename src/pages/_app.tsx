import { ClerkProvider } from "@clerk/nextjs";
import type { AppProps } from "next/app";
import "../styles/globals.css";

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ClerkProvider
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
      appearance={{
        variables: { colorPrimary: "#000000" },
      }}
    >
      <Component {...pageProps} />
    </ClerkProvider>
  );
}
