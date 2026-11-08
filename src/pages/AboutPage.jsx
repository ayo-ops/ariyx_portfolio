import React from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import SectionHeader from "../components/common/SectionHeader";
import ScrollReveal from "../components/common/ScrollReveal";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import { CONTACT } from "../data/navigation";
import { PLATFORMS } from "../data/platforms";
import {
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Briefcase,
  ArrowUpRight,
  Database,
  Cpu,
  Layers,
  Sparkles,
  Link as LinkIcon,
} from "lucide-react";

export default function AboutPage() {
  const VALUES = [
    {
      title: "Data Hygiene Over Tag Clutter",
      desc: "Most CRM systems devolve into chaos with 200+ disorganized tags and conflicting fields. We structure strict custom field taxonomies and logical schemas that your team can effortlessly navigate.",
      icon: Database,
      accent: "teal",
    },
    {
      title: "Pragmatic Architecture Over Hype",
      desc: "We don't build automation for the sake of complexity. Every workflow, webhook trigger, and Voice AI prompt must directly cut manual hours, increase response speed, or prevent pipeline leakage.",
      icon: Cpu,
      accent: "electric",
    },
    {
      title: "Direct Engineering Access",
      desc: "You collaborate directly with a systems architect who understands business operations and code. No junior account managers, no game of telephone, and no disconnected handoffs.",
      icon: Layers,
      accent: "teal",
    },
    {
      title: "Human-Calibrated AI Touchpoints",
      desc: "AI voice and conversational agents should enhance human relationships, not frustrate high-value prospects. We calibrate conversational thresholds with strict guardrails and seamless live human warm-transfers.",
      icon: Sparkles,
      accent: "electric",
    },
  ];

  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />

      <main className="pt-28 sm:pt-36 pb-24">
        {/* Page Header */}
        <section className="relative px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-20 text-center">
          <ScrollReveal delay={0}>
            <div className="inline-flex mb-4">
              <Badge variant="teal" icon={ShieldCheck} size="md">
                Consultancy Overview
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
              Systems Architecture for Businesses That Value{" "}
              <span className="text-teal">Operational Clarity.</span>
            </h1>
            <p className="mt-6 text-[16.5px] sm:text-[18px] text-soft-muted max-w-2xl mx-auto leading-relaxed font-normal">
              Ariyx Systems was founded on a simple premise: growing businesses don't need another generic marketing agency. They need cohesive, dependable CRM, automation, and AI infrastructure that operates without friction.
            </p>
          </ScrollReveal>
        </section>

        {/* Founder In-Depth Feature */}
        <section className="relative px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-28">
          <div className="rounded-3xl border border-deep-blue bg-midnight-dark/95 p-8 sm:p-12 lg:p-16 shadow-2xl">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
              
              {/* Photo Column */}
              <div className="lg:col-span-5">
                <ScrollReveal delay={100}>
                  <div className="relative mx-auto max-w-sm lg:max-w-none">
                    <div className="relative aspect-[3/4] sm:aspect-[4/5] rounded-2xl overflow-hidden border border-deep-blue bg-midnight shadow-2xl">
                      <img
                        src="/founder.jpg"
                        alt="Ariyo Emmanuel, Founder & Systems Consultant at Ariyx Systems"
                        className="w-full h-full object-cover object-top"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-midnight-dark/90 via-transparent to-transparent pointer-events-none" />
                      
                      <div className="absolute bottom-4 left-4 right-4 p-4 rounded-xl bg-midnight/90 backdrop-blur-md border border-deep-blue">
                        <div className="text-lg font-bold text-white">Ariyo Emmanuel</div>
                        <div className="text-xs font-mono text-teal font-medium mt-0.5">
                          Founder &amp; Systems Consultant
                        </div>
                      </div>
                    </div>
                  </div>
                </ScrollReveal>
              </div>

              {/* Story & Background */}
              <div className="lg:col-span-7 space-y-6">
                <ScrollReveal delay={180}>
                  <div className="font-mono text-xs uppercase tracking-wider text-teal font-semibold">
                    The Story Behind Ariyx Systems
                  </div>
                  <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-snug mt-2">
                    Bridging the Gap Between Surface Design &amp; Real Business Systems.
                  </h2>
                </ScrollReveal>

                <ScrollReveal delay={240}>
                  <p className="text-[16px] sm:text-[17.5px] text-soft-muted leading-relaxed font-normal">
                    Having spent years working inside CRM environments, workflow engines, and funnel platforms, I noticed a consistent pattern: companies would spend thousands of dollars on beautiful websites and funnels, only to let high-intent leads leak out because their back-end systems were broken.
                  </p>
                </ScrollReveal>

                <ScrollReveal delay={300}>
                  <p className="text-[16px] sm:text-[17.5px] text-soft-muted leading-relaxed font-normal">
                    Inquiries would sit in unmonitored inboxes. Pipelines were cluttered with outdated tags. Sales reps forgot follow-ups. And teams wasted countless hours manually typing customer data between disconnected platforms.
                  </p>
                </ScrollReveal>

                <ScrollReveal delay={360}>
                  <p className="text-[16px] sm:text-[17.5px] text-soft-muted leading-relaxed font-normal">
                    I established Ariyx Systems to solve that exact problem. We design end-to-end operational systems where the public-facing touchpoints (websites, funnels, webforms) connect seamlessly into intelligent CRM pipelines, automated follow-up sequences, and AI communication agents.
                  </p>
                </ScrollReveal>

                <ScrollReveal delay={420}>
                  <div className="pt-4 flex flex-wrap items-center gap-4">
                    <Button
                      href={CONTACT.calendlyUrl}
                      target="_blank"
                      variant="primary"
                      size="md"
                      icon={Calendar}
                    >
                      Schedule a Systems Call
                    </Button>
                    <a
                      href={CONTACT.linkedin}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 text-sm font-semibold text-soft-white hover:text-teal font-mono transition-colors"
                    >
                      <LinkIcon className="w-4 h-4 text-electric" /> LinkedIn Profile <ArrowUpRight className="w-4 h-4" />
                    </a>
                    <a
                      href={CONTACT.upwork}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 text-sm font-semibold text-soft-white hover:text-teal font-mono transition-colors"
                    >
                      <Briefcase className="w-4 h-4 text-teal" /> Upwork Verified <ArrowUpRight className="w-4 h-4" />
                    </a>
                  </div>
                </ScrollReveal>
              </div>

            </div>
          </div>
        </section>

        {/* Consulting Values Grid */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-28">
          <ScrollReveal delay={0}>
            <SectionHeader
              badge="Consulting Principles"
              badgeVariant="electric"
              title="How We Approach Every"
              highlightText="Systems Engagement."
              highlightColor="electric"
              description="Our work is guided by disciplined engineering practices focused on longevity, stability, and ease of adoption for your team."
            />
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            {VALUES.map((val, idx) => {
              const Icon = val.icon;
              const isTeal = val.accent === "teal";
              return (
                <ScrollReveal key={val.title} delay={idx * 80}>
                  <div className="h-full rounded-2xl border border-deep-blue bg-midnight/80 p-8 hover:border-electric/60 hover:-translate-y-1 transition-all duration-300 shadow-card">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 border ${
                        isTeal
                          ? "bg-teal-subtle border-teal/40 text-teal"
                          : "bg-electric-subtle border-electric/40 text-electric-light"
                      }`}
                    >
                      <Icon className="w-6 h-6" strokeWidth={1.8} />
                    </div>
                    <h3 className="text-2xl font-bold text-white tracking-tight mb-3">
                      {val.title}
                    </h3>
                    <p className="text-[15px] sm:text-[16px] text-soft-muted leading-relaxed font-normal">
                      {val.desc}
                    </p>
                  </div>
                </ScrollReveal>
              );
            })}
          </div>
        </section>

        {/* Tech Ecosystem Banner */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16">
          <ScrollReveal delay={0}>
            <div className="rounded-2xl border border-deep-blue bg-midnight-dark p-8 sm:p-12 text-center">
              <span className="font-mono text-xs uppercase tracking-[0.22em] text-soft-dim font-medium block mb-4">
                Core Implementation Ecosystem
              </span>
              <h3 className="text-2xl sm:text-3xl font-bold text-white max-w-2xl mx-auto mb-6">
                Engineered Across the Best Platforms in Modern Automation
              </h3>
              <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 max-w-4xl mx-auto">
                {PLATFORMS.map((p) => (
                  <div
                    key={p.name}
                    className="px-4 py-2 rounded-xl bg-midnight border border-deep-blue font-mono text-xs sm:text-[13.5px] text-soft-white font-medium"
                  >
                    {p.name} <span className="text-soft-dim font-normal">· {p.role}</span>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>
        </section>

      </main>

      <Footer />
    </div>
  );
}
