import React, { useState } from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import SectionHeader from "../components/common/SectionHeader";
import ScrollReveal from "../components/common/ScrollReveal";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import { INSIGHT_CATEGORIES, UPCOMING_TOPICS } from "../data/insights";
import { CONTACT } from "../data/navigation";
import { APPS_SCRIPT_ENDPOINT } from "../data/api";
import {
  BookOpen,
  Calendar,
  Clock,
  Sparkles,
  ArrowRight,
  Mail,
  CheckCircle2,
  Terminal,
  Loader2,
  AlertCircle,
} from "lucide-react";

export default function InsightsPage() {
  const [activeCategory, setActiveCategory] = useState("All Insights");
  const [emailInput, setEmailInput] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const filteredTopics =
    activeCategory === "All Insights"
      ? UPCOMING_TOPICS
      : UPCOMING_TOPICS.filter((t) => t.category === activeCategory);

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    // Spam honeypot: if filled, silently act like it succeeded without calling backend
    if (honeypot.trim() !== "") {
      setIsSubmitting(true);
      setTimeout(() => {
        setIsSubmitting(false);
        setSubscribed(true);
      }, 700);
      return;
    }

    const trimmedEmail = emailInput.trim();
    if (!trimmedEmail) {
      setErrorMessage("Please enter your business email address.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setErrorMessage("Please enter a valid email address.");
      return;
    }

    if (trimmedEmail.length > 150) {
      setErrorMessage("Email must be 150 characters or less.");
      return;
    }

    // Cooldown rate-limit (60s)
    const COOLDOWN_MS = 60000;
    const lastSent = localStorage.getItem("ariyx_last_newsletter_ts");
    if (lastSent) {
      const elapsed = Date.now() - parseInt(lastSent, 10);
      if (elapsed < COOLDOWN_MS) {
        const remaining = Math.ceil((COOLDOWN_MS - elapsed) / 1000);
        setErrorMessage(
          `A subscription was recently submitted. Please wait ${remaining}s before trying again.`
        );
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const payload = {
        action: "subscribe",
        email: trimmedEmail.slice(0, 150),
      };

      const response = await fetch(APPS_SCRIPT_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "text/plain;charset=utf-8",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result && result.success === true) {
        try {
          localStorage.setItem("ariyx_last_newsletter_ts", Date.now().toString());
        } catch (_) {}
        setSubscribed(true);
      } else {
        setErrorMessage(
          result?.message ||
            "Unable to subscribe at this moment. Please try again later or reach out directly."
        );
      }
    } catch (err) {
      console.error("Newsletter subscription error:", err);
      setErrorMessage(
        "Network connection issue. Please check your internet connection or try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />

      <main className="pt-28 sm:pt-36 pb-24">
        {/* Header Section */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16 text-center">
          <ScrollReveal delay={0}>
            <div className="inline-flex mb-4">
              <Badge variant="teal" icon={BookOpen} size="md">
                Systems &amp; Architecture Insights
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
              Practical Engineering Blueprints &amp;{" "}
              <span className="text-teal">Operational Teardowns.</span>
            </h1>
            <p className="mt-6 text-[16.5px] sm:text-[18px] text-soft-muted max-w-3xl mx-auto leading-relaxed font-normal">
              Tactical teardowns and implementation frameworks on CRM data modeling, webhook middleware, and Voice AI agents—written directly from real production client builds.
            </p>
          </ScrollReveal>
        </section>

        {/* Categories Filter */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-12">
          <ScrollReveal delay={80}>
            <div className="flex flex-wrap items-center justify-center gap-2.5">
              {INSIGHT_CATEGORIES.map((category) => (
                <button
                  key={category}
                  onClick={() => setActiveCategory(category)}
                  className={`px-5 py-2.5 rounded-full font-mono text-xs sm:text-[13px] font-semibold transition-all border cursor-pointer ${
                    activeCategory === category
                      ? "bg-teal text-midnight-dark border-teal shadow-teal"
                      : "bg-midnight-dark text-soft-muted border-deep-blue hover:border-white/20 hover:text-white"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </ScrollReveal>
        </section>

        {/* Editorial Architecture Roadmap / Upcoming Blueprints */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-24">
          <div className="space-y-6">
            {filteredTopics.map((topic, idx) => (
              <ScrollReveal key={topic.id} delay={idx * 60}>
                <div className="rounded-2xl border border-deep-blue bg-midnight-dark/95 p-6 sm:p-8 hover:border-teal/50 transition-all duration-300 shadow-card">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    
                    <div className="space-y-3 max-w-3xl">
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="font-mono text-xs px-2.5 py-1 rounded bg-deep-blue/60 text-teal font-semibold">
                          {topic.category}
                        </span>
                        <span className="font-mono text-xs text-soft-dim">
                          {topic.format} · {topic.estimatedReadTime}
                        </span>
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-electric-subtle text-electric-light border border-electric/30">
                          {topic.status}
                        </span>
                      </div>

                      <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
                        {topic.title}
                      </h2>

                      <p className="text-[15px] sm:text-[15.5px] text-soft-muted leading-relaxed font-normal">
                        {topic.summary}
                      </p>

                      <div className="flex flex-wrap gap-2 pt-1">
                        {topic.tags.map((t) => (
                          <span
                            key={t}
                            className="font-mono text-[11px] px-2 py-0.5 rounded bg-midnight border border-deep-blue text-soft-dim"
                          >
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="shrink-0 flex items-center">
                      <a
                        href={CONTACT.calendlyUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 text-xs font-mono font-bold text-teal hover:text-teal-light transition-colors"
                      >
                        <span>Discuss This Topic</span>
                        <ArrowRight className="w-4 h-4" />
                      </a>
                    </div>

                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </section>

        {/* Newsletter / Briefing Box */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
          <ScrollReveal delay={0}>
            <div className="rounded-3xl border border-deep-blue bg-midnight p-8 sm:p-12 text-center shadow-2xl relative overflow-hidden">
              <div className="w-12 h-12 rounded-xl bg-teal-subtle border border-teal/40 text-teal mx-auto flex items-center justify-center mb-4">
                <Terminal className="w-6 h-6" />
              </div>

              <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                The Ariyx Systems Briefing
              </h3>

              <p className="mt-3 text-[15px] sm:text-[16px] text-soft-muted max-w-xl mx-auto leading-relaxed">
                Direct architectural breakdowns, webhook logic patterns, and CRM automation blueprints delivered monthly. No marketing fluff or surface-level tips.
              </p>

              {subscribed ? (
                <div className="mt-6 p-4 rounded-xl bg-teal-subtle border border-teal/40 text-teal font-mono text-sm max-w-md mx-auto flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-5 h-5 shrink-0" />
                  <span>Thank you. You will receive new systems blueprints as they publish.</span>
                </div>
              ) : (
                <form
                  onSubmit={handleSubscribe}
                  noValidate
                  className="mt-6 max-w-md mx-auto"
                >
                  {/* Spam honeypot */}
                  <div
                    aria-hidden="true"
                    style={{
                      position: "absolute",
                      left: "-9999px",
                      opacity: 0,
                      pointerEvents: "none",
                      height: 0,
                    }}
                  >
                    <label htmlFor="newsletter-website">Website</label>
                    <input
                      type="text"
                      id="newsletter-website"
                      name="website"
                      tabIndex={-1}
                      autoComplete="off"
                      value={honeypot}
                      onChange={(e) => setHoneypot(e.target.value)}
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                    <input
                      type="email"
                      required
                      placeholder="Enter your business email"
                      value={emailInput}
                      onChange={(e) => setEmailInput(e.target.value)}
                      disabled={isSubmitting}
                      className="w-full px-4 py-3 rounded-full bg-midnight-dark border border-deep-blue text-soft-white placeholder-soft-dim text-sm focus:outline-none focus:border-teal transition-colors font-mono disabled:opacity-50"
                    />
                    <Button
                      type="submit"
                      variant="teal"
                      size="md"
                      disabled={isSubmitting}
                      className="shrink-0 w-full sm:w-auto inline-flex items-center justify-center gap-2"
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Subscribing...</span>
                        </>
                      ) : (
                        "Subscribe"
                      )}
                    </Button>
                  </div>

                  {errorMessage && (
                    <div className="mt-3 flex items-center justify-center gap-2 text-rose-400 text-xs font-mono">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{errorMessage}</span>
                    </div>
                  )}
                </form>
              )}
            </div>
          </ScrollReveal>
        </section>
      </main>

      <Footer />
    </div>
  );
}
