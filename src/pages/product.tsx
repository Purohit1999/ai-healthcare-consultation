"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { useAuth, UserButton } from "@clerk/nextjs";
import { fetchEventSource } from "@microsoft/fetch-event-source";

/*
  🔒 Billing components — COMMENTED for now
  Uncomment later when enabling subscriptions
*/
// import { Protect, PricingTable } from "@clerk/nextjs";

function IdeaGenerator() {
  const { getToken, isSignedIn } = useAuth();
  const [idea, setIdea] = useState<string>("…loading");

  useEffect(() => {
    let buffer = "";
    const controller = new AbortController();

    (async () => {
      if (!isSignedIn) {
        setIdea("Authentication required");
        return;
      }

      const jwt = await getToken();
      if (!jwt) {
        setIdea("Authentication required");
        return;
      }

      await fetchEventSource("/api", {
        headers: { Authorization: `Bearer ${jwt}` },
        signal: controller.signal,

        onmessage(ev) {
          if (ev.data === "[DONE]") return;
          buffer += ev.data;
          setIdea(buffer);
        },

        onerror(err) {
          console.error("SSE error:", err);
          // fetch-event-source will retry automatically
        },
      });
    })();

    return () => controller.abort();
  }, [getToken, isSignedIn]);

  return (
    <div className="container mx-auto px-4 py-12">
      <header className="text-center mb-12">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
          Business Idea Generator
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          AI-powered innovation at your fingertips
        </p>
      </header>

      <div className="max-w-3xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          {idea === "…loading" ? (
            <div className="flex items-center justify-center py-12 text-gray-400 animate-pulse">
              Generating your business idea...
            </div>
          ) : (
            <div className="markdown-content text-gray-700 dark:text-gray-300">
              <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                {idea}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Product() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* User menu */}
      <div className="absolute top-4 right-4">
        <UserButton showName />
      </div>

      {/*
        🔒 Subscription protection — COMMENTED
        Uncomment when real billing plans exist

      <Protect
        plan="premium_subscription"
        fallback={
          <div className="container mx-auto px-4 py-12">
            <header className="text-center mb-12">
              <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
                Choose Your Plan
              </h1>
              <p className="text-gray-600 dark:text-gray-400 text-lg mb-8">
                Unlock unlimited AI-powered business ideas
              </p>
            </header>

            <div className="max-w-4xl mx-auto">
              <PricingTable />
            </div>
          </div>
        }
      >
        <IdeaGenerator />
      </Protect>
      */}

      {/* ✅ Experimental mode: everyone gets access */}
      <IdeaGenerator />
    </main>
  );
}
