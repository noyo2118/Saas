import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Shield, Mail, ArrowRight, ArrowLeft, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Aurora, CyberGrid, NoiseOverlay } from "@/components/effects/Backgrounds";
import { ParticleField } from "@/components/effects/ParticleField";
import { ThreatGlobe } from "@/components/viz/ThreatGlobe";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { NeonButton } from "@/components/ui-custom/NeonButton";
import { GlowBadge } from "@/components/ui-custom/GlowBadge";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — TrustScan" },
      { name: "description", content: "Sign in to your TrustScan command center with a one-time email code." },
      { property: "og:title", content: "Sign in — TrustScan" },
      { property: "og:description", content: "Passwordless access via one-time email code." },
    ],
  }),
  component: () => <AuthPage />,
});

export function AuthPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<"email" | "otp">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  const sendCode = async (resend = false) => {
    setError(null);
    setInfo(null);
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        shouldCreateUser: true,
        emailRedirectTo: `${window.location.origin}/dashboard`,
      },
    });
    setLoading(false);
    if (error) {
      setError(error.message);
      return;
    }
    setStep("otp");
    setCooldown(30);
    setInfo(resend ? "A new code has been sent." : null);
  };

  const verifyCode = async () => {
    setError(null);
    if (code.length !== 6) {
      setError("Enter the 6-digit code from your email.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.verifyOtp({
      email,
      token: code,
      type: "email",
    });
    setLoading(false);
    if (error) {
      setError(error.message);
      return;
    }
    navigate({ to: "/dashboard" });
  };

  return (
    <div className="relative grid min-h-screen overflow-hidden lg:grid-cols-2">
      {/* Left immersive panel */}
      <div className="relative hidden overflow-hidden lg:block">
        <Aurora />
        <CyberGrid />
        <ParticleField />
        <NoiseOverlay />
        <div className="relative flex h-full flex-col justify-between p-10">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-display text-base font-semibold">TrustScan</span>
          </Link>
          <div className="flex flex-1 items-center justify-center">
            <ThreatGlobe size={420} />
          </div>
          <div className="max-w-sm">
            <GlowBadge tone="cyan">Live · v4.2</GlowBadge>
            <p className="mt-4 font-display text-2xl leading-tight">
              "We catch phishing kits hours before our previous platform."
            </p>
            <p className="mt-2 text-sm text-muted-foreground">Jonas Reiter · Head of SecOps, Vertex Labs</p>
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="relative flex items-center justify-center p-6 lg:p-10">
        <Aurora className="lg:hidden" />
        <GlassCard variant="holographic" className="relative w-full max-w-md p-8">
          <div className="mb-7">
            <h1 className="font-display text-3xl font-semibold tracking-tight">
              {step === "email" ? "Sign in to TrustScan" : "Enter your code"}
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {step === "email"
                ? "We'll email you a 6-digit code. No password needed."
                : <>Sent to <span className="text-foreground/85">{email}</span>. Check your inbox.</>}
            </p>
          </div>

          {step === "email" ? (
            <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); sendCode(false); }}>
              <label className="block">
                <span className="mb-1.5 block text-xs uppercase tracking-[0.18em] text-muted-foreground">Work email</span>
                <span className="relative flex items-center">
                  <Mail className="pointer-events-none absolute left-3 h-4 w-4 text-muted-foreground" />
                  <input
                    type="email"
                    autoComplete="email"
                    autoFocus
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="h-11 w-full rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:border-[color-mix(in_oklab,var(--neon-cyan)_50%,var(--border))] focus:outline-none focus:ring-2 focus:ring-[color-mix(in_oklab,var(--neon-cyan)_25%,transparent)]"
                  />
                </span>
              </label>

              {error && <p className="text-sm text-neon-red">{error}</p>}

              <NeonButton type="submit" className="w-full" disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Send code <ArrowRight className="h-4 w-4" /></>}
              </NeonButton>
              <NeonButton variant="ghost" type="button" className="w-full" asChild>
                <Link to="/">Cancel</Link>
              </NeonButton>
            </form>
          ) : (
            <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); verifyCode(); }}>
              <div className="flex justify-center">
                <InputOTP maxLength={6} value={code} onChange={setCode} autoFocus>
                  <InputOTPGroup>
                    {[0, 1, 2, 3, 4, 5].map((i) => (
                      <InputOTPSlot key={i} index={i} />
                    ))}
                  </InputOTPGroup>
                </InputOTP>
              </div>

              {info && <p className="text-center text-sm text-neon-cyan">{info}</p>}
              {error && <p className="text-center text-sm text-neon-red">{error}</p>}

              <NeonButton type="submit" className="w-full" disabled={loading || code.length !== 6}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Verify & sign in <ArrowRight className="h-4 w-4" /></>}
              </NeonButton>

              <div className="flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={() => { setStep("email"); setCode(""); setError(null); setInfo(null); }}
                  className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
                >
                  <ArrowLeft className="h-3 w-3" /> Use a different email
                </button>
                <button
                  type="button"
                  disabled={cooldown > 0 || loading}
                  onClick={() => sendCode(true)}
                  className="text-neon-cyan hover:underline disabled:cursor-not-allowed disabled:text-muted-foreground disabled:no-underline"
                >
                  {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
                </button>
              </div>

              <NeonButton variant="ghost" type="button" className="w-full" asChild>
                <Link to="/">Cancel</Link>
              </NeonButton>
            </form>
          )}

          <p className="mt-6 text-center text-xs text-muted-foreground">
            By continuing you agree to TrustScan's terms and privacy policy.
          </p>
        </GlassCard>
      </div>
    </div>
  );
}
