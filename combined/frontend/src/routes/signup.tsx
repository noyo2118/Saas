import { createFileRoute } from "@tanstack/react-router";
import { AuthPage } from "./login";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [
      { title: "Create account — TrustScan" },
      { name: "description", content: "Spin up your free TrustScan console in seconds." },
      { property: "og:title", content: "Create account — TrustScan" },
      { property: "og:description", content: "Free tier — no credit card required." },
    ],
  }),
  component: () => <AuthPage />,
});
