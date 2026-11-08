import React from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import SectionHeader from "../components/common/SectionHeader";
import ScrollReveal from "../components/common/ScrollReveal";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import { SOLUTIONS } from "../data/solutions";
import { CONTACT } from "../data/navigation";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  ArrowRight,
  Workflow,
  Zap,
} from "lucide-react";

export default function SolutionsPage() {
  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />

      <main className="pt-28 sm:pt-36 pb-24">
        {/* Header Section */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-20 text-center">
          <ScrollReveal delay={0}>
            <div className="inline-flex mb-4">
              <Badge variant="teal" icon={Workflow} size="md">
                Operational Problem Solving
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
              Engineered Solutions for{" "}
              <span className="text-teal">Critical Business Bottlenecks.</span>
            </h1>
            <p className="mt-6 text-[16.5px] sm:text-[18px] text-soft-muted max-w-3xl mx-auto leading-relaxed font-normal">
              Most businesses lose revenue not from a lack of market demand, but from operational friction: delayed responses, abandoned follow-ups, empty calendars, and disconnected tools. Here is how our architectures solve each failure point.
            </p>
          </ScrollReveal>
        </section>

        {/* 5 Problem-Solution Deep Dive Cards */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-24 space-y-16">
          {SOLUTIONS.map((item) => {
            const isTeal = item.accent === "teal";

            return (
              <ScrollReveal key={item.id} delay={60}>
                <div
                  id={item.id}
                  className="rounded-3xl border border-deep-blue bg-midnight-dark/95 p-8 sm:p-12 shadow-2xl relative overflow-hidden"
                >
                  {/* Top Problem vs Solution Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-6 border-b border-deep-blue/80">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-2xl font-black text-teal">
                        {item.problemNumber}
                      </span>
                      <span className="font-mono text-xs uppercase tracking-wider text-soft-dim px-3 py-1 rounded bg-deep-blue/40 border border-deep-blue font-semibold">
                        {item.tag}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {item.technicalHighlights.map((tech) => (
                        <span
                          key={tech}
                          className="font-mono text-xs px-2.5 py-1 rounded bg-midnight border border-deep-blue text-soft-white font-medium"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-start">
                    
                    {/* The Friction / Problem Column */}
                    <div className="lg:col-span-5 space-y-4 rounded-2xl bg-midnight p-6 sm:p-8 border border-deep-blue/80">
                      <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-red-400 font-semibold">
                        <ShieldAlert className="w-4 h-4" /> The Operational Breakdown
                      </div>
                      <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
                        {item.problemTitle}
                      </h3>
                      <p className="text-[15px] sm:text-[15.5px] text-soft-muted leading-relaxed font-normal">
                        {item.problemDesc}
                      </p>
                      <div className="p-3.5 rounded-xl bg-midnight-dark border border-red-500/20 text-xs font-mono text-red-300">
                        <span className="font-bold">Business Cost: </span>
                        {item.impact}
                      </div>
                    </div>

                    {/* The Ariyx Architecture / Solution Column */}
                    <div className="lg:col-span-7 space-y-5">
                      <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-teal font-semibold">
                        <ShieldCheck className="w-4 h-4" /> The Ariyx Systems Fix
                      </div>
                      
                      <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
                        {item.solutionTitle}
                      </h3>

                      <p className="text-[16px] sm:text-[17px] text-soft-muted leading-relaxed font-normal">
                        {item.solutionDesc}
                      </p>

                      <div className="space-y-3 pt-2">
                        <span className="font-mono text-xs uppercase tracking-wider text-soft-dim block font-medium">
                          Automated Flow Execution:
                        </span>
                        {item.workflowSteps.map((step, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/60 text-sm sm:text-[14.5px] text-soft-white font-medium"
                          >
                            <CheckCircle2
                              className={`w-4 h-4 mt-0.5 shrink-0 ${
                                isTeal ? "text-teal" : "text-electric-light"
                              }`}
                            />
                            <span className="leading-snug">{step}</span>
                          </div>
                        ))}
                      </div>

                      <div className="pt-4">
                        <Button
                          href={CONTACT.calendlyUrl}
                          target="_blank"
                          variant="primary"
                          size="md"
                          icon={Calendar}
                        >
                          Resolve This Bottleneck
                        </Button>
                      </div>
                    </div>

                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </section>

        {/* Bottom Assessment Callout */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <ScrollReveal delay={0}>
            <div className="rounded-3xl border border-deep-blue bg-midnight p-8 sm:p-14 text-center shadow-2xl">
              <h3 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Ready to stop letting qualified leads slip through the cracks?
              </h3>
              <p className="mt-4 text-[16px] sm:text-[17.5px] text-soft-muted max-w-2xl mx-auto leading-relaxed">
                Schedule a 30-minute systems discovery call with Ariyo Emmanuel. We will audit your current pipeline and map the automated workflows required to fix your leaks.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button
                  href={CONTACT.calendlyUrl}
                  target="_blank"
                  variant="teal"
                  size="lg"
                  icon={Calendar}
                >
                  Schedule a Systems Audit Call
                </Button>
                <Button
                  href={CONTACT.whatsappUrl}
                  target="_blank"
                  variant="outline"
                  size="lg"
                >
                  Direct WhatsApp Chat
                </Button>
              </div>
            </div>
          </ScrollReveal>
        </section>
      </main>

      <Footer />
    </div>
  );
}
