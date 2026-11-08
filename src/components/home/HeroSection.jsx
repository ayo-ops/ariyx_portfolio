import React, { useState, useEffect } from "react";
import Button from "../common/Button";
import Badge from "../common/Badge";
import ScrollReveal from "../common/ScrollReveal";
import { CONTACT } from "../../data/navigation";
import {
  Calendar,
  Sparkles,
  Bot,
  Zap,
  CheckCircle,
  Activity,
  ArrowRight,
  PhoneCall,
  Database,
} from "lucide-react";

export default function HeroSection() {
  const [eventIndex, setEventIndex] = useState(0);

  const LIVE_EVENTS = [
    {
      title: "Qualified Webform Inbound",
      meta: "Paid Search · ID #LEAD-8842",
      stage1: "0.12s",
      stage2: "0.84s",
      stage3: "Active",
      time: "Just now",
    },
    {
      title: "Inbound AI Voice Qualification",
      meta: "Direct Phone Line · #CALL-4209",
      stage1: "0.08s",
      stage2: "0.45s",
      stage3: "Connected",
      time: "2s ago",
    },
    {
      title: "High-Ticket Lead Reactivation",
      meta: "CRM Pipeline Trigger · #REENG-108",
      stage1: "0.15s",
      stage2: "0.92s",
      stage3: "Booked",
      time: "5s ago",
    },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setEventIndex((prev) => (prev + 1) % LIVE_EVENTS.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const currentEvent = LIVE_EVENTS[eventIndex];

  return (
    <section className="relative pt-32 sm:pt-40 pb-20 sm:pb-28 overflow-hidden tech-grid">
      {/* Background radial gradient accent (restrained) */}
      <div
        className="pointer-events-none absolute top-10 left-1/2 -translate-x-1/2 w-[850px] h-[520px] rounded-full opacity-20 blur-3xl -z-10"
        style={{
          background: "radial-gradient(ellipse at center, #243B60 0%, #101B2D 70%)",
        }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Hero Left Content */}
          <div className="lg:col-span-7 space-y-6">
            <ScrollReveal delay={0}>
              <Badge variant="teal" icon={Sparkles} size="sm">
                CRM, Automation &amp; AI Systems Consultancy
              </Badge>
            </ScrollReveal>

            <ScrollReveal delay={80}>
              <h1 className="text-4xl sm:text-5xl lg:text-[52px] xl:text-[58px] font-extrabold tracking-tight text-white leading-[1.12]">
                Intelligent Systems That{" "}
                <span className="text-teal">Streamline Operations</span> &amp; Scale Revenue.
              </h1>
            </ScrollReveal>

            <ScrollReveal delay={160}>
              <p className="text-[16.5px] sm:text-[18px] text-soft-muted max-w-2xl leading-relaxed font-normal">
                We architect custom CRM pipelines, autonomous workflows, and AI communication systems for growing businesses—eliminating manual friction and ensuring every lead moves seamlessly toward a closed deal.
              </p>
            </ScrollReveal>

            <ScrollReveal delay={240}>
              <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <Button
                  href={CONTACT.calendlyUrl}
                  target="_blank"
                  variant="primary"
                  size="lg"
                  icon={Calendar}
                >
                  Schedule a Consultation
                </Button>
                <Button
                  href="/services"
                  variant="secondary"
                  size="lg"
                  showArrow
                >
                  Explore Services
                </Button>
              </div>
            </ScrollReveal>

            {/* Credibility micro-indicators */}
            <ScrollReveal delay={320}>
              <div className="pt-6 grid grid-cols-3 gap-6 border-t border-deep-blue/80 max-w-xl">
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold font-mono text-white">
                    &lt; 60s
                  </div>
                  <div className="text-xs sm:text-[13px] text-soft-dim font-medium mt-1">
                    Speed-to-Lead Response
                  </div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold font-mono text-teal">
                    100%
                  </div>
                  <div className="text-xs sm:text-[13px] text-soft-dim font-medium mt-1">
                    Pipeline Attribution
                  </div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold font-mono text-electric-light">
                    Zero
                  </div>
                  <div className="text-xs sm:text-[13px] text-soft-dim font-medium mt-1">
                    Manual Bottlenecks
                  </div>
                </div>
              </div>
            </ScrollReveal>
          </div>

          {/* Hero Right Visual: Systems Architecture Console with Animated Connections */}
          <div className="lg:col-span-5">
            <ScrollReveal delay={200}>
              <div className="relative rounded-2xl border border-deep-blue bg-midnight-dark/95 shadow-2xl overflow-hidden backdrop-blur-sm">
                
                {/* Terminal / Console Bar */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-deep-blue bg-midnight/90">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-teal/80" />
                    <span className="ml-2 font-mono text-xs text-soft-dim">
                      ariyx.engine // pipeline-sync
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-xs text-teal font-medium">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-teal" />
                    </span>
                    System Live
                  </div>
                </div>

                {/* Console Body */}
                <div className="p-5 sm:p-6 space-y-4">
                  {/* Event Simulation Header */}
                  <div className="bg-midnight rounded-xl p-3.5 border border-deep-blue flex items-center justify-between transition-all duration-300">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-electric-subtle border border-electric/40 flex items-center justify-center">
                        <Zap className="w-4 h-4 text-electric-light" />
                      </div>
                      <div>
                        <div className="text-xs sm:text-sm font-mono text-white font-semibold">
                          Live Event: {currentEvent.title}
                        </div>
                        <div className="text-xs text-soft-dim font-mono">
                          {currentEvent.meta} · <span className="text-teal font-medium">{currentEvent.time}</span>
                        </div>
                      </div>
                    </div>
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-teal-subtle text-teal font-medium border border-teal/30">
                      Auto-Routed
                    </span>
                  </div>

                  {/* Pipeline Flow Stages with Animated Trace */}
                  <div className="relative space-y-3 font-mono text-xs">
                    {/* Visual Connecting SVG Wire */}
                    <svg
                      className="absolute left-[17px] top-6 bottom-6 w-1 h-[78%] pointer-events-none z-0 overflow-visible"
                    >
                      <line
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="100%"
                        stroke="#243B60"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                        className="dash-flow"
                      />
                    </svg>

                    {/* Step 1 */}
                    <div className="relative z-10 flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/60 hover:border-teal/40 transition-colors">
                      <div className="w-7 h-7 rounded-full bg-teal-subtle border border-teal/50 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                        <CheckCircle className="w-4 h-4 text-teal" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-soft-white font-semibold text-xs sm:text-[13px]">
                            01. Data Hygiene &amp; Schema Match
                          </span>
                          <span className="text-soft-dim text-xs font-mono">{currentEvent.stage1}</span>
                        </div>
                        <p className="text-xs sm:text-[13px] text-soft-muted font-sans mt-0.5 leading-snug">
                          Deduplicated in CRM, custom fields parsed &amp; deal score assigned.
                        </p>
                      </div>
                    </div>

                    {/* Step 2 */}
                    <div className="relative z-10 flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/60 hover:border-teal/40 transition-colors">
                      <div className="w-7 h-7 rounded-full bg-teal-subtle border border-teal/50 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                        <CheckCircle className="w-4 h-4 text-teal" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-soft-white font-semibold text-xs sm:text-[13px]">
                            02. Instant SMS / WhatsApp Touch
                          </span>
                          <span className="text-soft-dim text-xs font-mono">{currentEvent.stage2}</span>
                        </div>
                        <p className="text-xs sm:text-[13px] text-soft-muted font-sans mt-0.5 leading-snug">
                          Speed-to-lead sequence triggered with self-booking calendar link.
                        </p>
                      </div>
                    </div>

                    {/* Step 3 */}
                    <div className="relative z-10 flex items-start gap-3 p-3 rounded-xl bg-electric-subtle/30 border border-electric/40">
                      <div className="w-7 h-7 rounded-full bg-electric/20 border border-electric flex items-center justify-center shrink-0 mt-0.5 shadow-highlight">
                        <Bot className="w-4 h-4 text-electric-light animate-pulse" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-electric-light font-semibold text-xs sm:text-[13px]">
                            03. Voice AI &amp; Calendar Lock
                          </span>
                          <span className="text-electric-light text-xs font-mono font-medium">
                            {currentEvent.stage3}
                          </span>
                        </div>
                        <p className="text-xs sm:text-[13px] text-soft-muted font-sans mt-0.5 leading-snug">
                          Calendar scheduled, round-robin rep assigned, reminders queued.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Console System Metrics Footer */}
                  <div className="pt-3 border-t border-deep-blue/80 flex items-center justify-between text-xs font-mono text-soft-dim">
                    <span className="flex items-center gap-2">
                      <Activity className="w-3.5 h-3.5 text-teal" />
                      API Endpoints Healthy
                    </span>
                    <span className="text-soft-muted font-medium">99.98% Reliability</span>
                  </div>
                </div>
              </div>
            </ScrollReveal>
          </div>

        </div>
      </div>
    </section>
  );
}
