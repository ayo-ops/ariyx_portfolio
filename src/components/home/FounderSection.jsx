import React from "react";
import SectionHeader from "../common/SectionHeader";
import ScrollReveal from "../common/ScrollReveal";
import Button from "../common/Button";
import { CONTACT } from "../../data/navigation";
import {
  Calendar,
  Briefcase,
  CheckCircle2,
  ShieldCheck,
  Terminal,
  ArrowUpRight,
  Link as LinkIcon,
} from "lucide-react";

export default function FounderSection() {
  return (
    <section id="about" className="py-24 sm:py-32 bg-midnight border-t border-deep-blue relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-center">
          
          {/* Founder Portrait Column */}
          <div className="lg:col-span-5">
            <ScrollReveal delay={0}>
              <div className="relative mx-auto max-w-md lg:max-w-none">
                
                {/* Ambient glow accent behind photo */}
                <div
                  className="pointer-events-none absolute -inset-4 rounded-3xl opacity-30 blur-2xl -z-10"
                  style={{
                    background: "radial-gradient(circle at center, #243B60 0%, transparent 70%)",
                  }}
                />

                {/* Professional Photo Frame */}
                <div className="relative aspect-[3/4] sm:aspect-[4/5] rounded-3xl overflow-hidden border border-deep-blue bg-midnight-dark shadow-2xl group">
                  <img
                    src="/founder.jpg"
                    alt="Ariyo Emmanuel, Founder & Systems Consultant at Ariyx Systems"
                    className="w-full h-full object-cover object-top transition-transform duration-700 ease-out group-hover:scale-[1.02]"
                    loading="lazy"
                  />

                  {/* Gradient shadow to anchor badge at bottom */}
                  <div className="absolute inset-0 bg-gradient-to-t from-midnight-dark/90 via-midnight/20 to-transparent pointer-events-none" />

                  {/* Status Overlay Badge */}
                  <div className="absolute bottom-5 left-5 right-5 p-4 rounded-2xl bg-midnight/90 backdrop-blur-md border border-deep-blue shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-base font-bold text-white tracking-tight">
                          Ariyo Emmanuel
                        </div>
                        <div className="text-xs font-mono text-teal font-medium mt-0.5">
                          Founder &amp; Systems Consultant
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <a
                          href={CONTACT.linkedin}
                          target="_blank"
                          rel="noreferrer"
                          className="w-8 h-8 rounded-lg bg-deep-blue/60 hover:bg-electric text-soft-white hover:text-white flex items-center justify-center transition-colors"
                          aria-label="LinkedIn profile"
                        >
                          <LinkIcon className="w-4 h-4" />
                        </a>
                        <a
                          href={CONTACT.upwork}
                          target="_blank"
                          rel="noreferrer"
                          className="w-8 h-8 rounded-lg bg-deep-blue/60 hover:bg-teal text-soft-white hover:text-midnight-dark flex items-center justify-center transition-colors"
                          aria-label="Upwork profile"
                        >
                          <Briefcase className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  </div>

                </div>

              </div>
            </ScrollReveal>
          </div>

          {/* Founder Story & Consulting Philosophy */}
          <div className="lg:col-span-7 space-y-6">
            <ScrollReveal delay={100}>
              <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.2em] text-teal">
                <ShieldCheck className="w-4 h-4" />
                Leadership &amp; Engineering Philosophy
              </div>

              <h2 className="text-3xl sm:text-4xl lg:text-[44px] font-extrabold tracking-tight text-white leading-[1.16] mt-3">
                Building Systems, <span className="text-teal">Not Just Surface-Level Websites.</span>
              </h2>
            </ScrollReveal>

            <ScrollReveal delay={180}>
              <p className="text-[16.5px] sm:text-[17.5px] text-soft-muted leading-relaxed font-normal">
                I founded Ariyx Systems with a direct, pragmatic mission: growing service businesses and digital platforms don't need another generic digital marketing agency or flashy, disconnected landing pages. They need <strong className="text-white font-semibold">robust, reliable operational systems</strong> that turn visitor attention into booked conversations and structured revenue.
              </p>
            </ScrollReveal>

            <ScrollReveal delay={260}>
              <p className="text-[16px] sm:text-[17px] text-soft-muted leading-relaxed font-normal">
                When you work with Ariyx Systems, you deal directly with a dedicated systems architect. We map your actual customer journey, design clean CRM data models without tag clutter, and wire automated follow-up workflows and Voice AI agents that support your human team without creating operational headaches.
              </p>
            </ScrollReveal>

            {/* Core Commitments Box */}
            <ScrollReveal delay={320}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2">
                <div className="p-4 rounded-xl bg-midnight-dark border border-deep-blue flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-teal mt-0.5 shrink-0" />
                  <div className="text-xs sm:text-sm text-soft-white font-medium">
                    <span className="font-semibold text-white block mb-0.5">Direct Technical Lead</span>
                    No junior account managers or outsourced handoffs.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-midnight-dark border border-deep-blue flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-electric-light mt-0.5 shrink-0" />
                  <div className="text-xs sm:text-sm text-soft-white font-medium">
                    <span className="font-semibold text-white block mb-0.5">Pragmatic Tool Selection</span>
                    GoHighLevel, n8n, Make &amp; Python chosen to fit your stack.
                  </div>
                </div>
              </div>
            </ScrollReveal>

            {/* CTA Buttons */}
            <ScrollReveal delay={380}>
              <div className="pt-3 flex flex-wrap items-center gap-4">
                <Button
                  href={CONTACT.calendlyUrl}
                  target="_blank"
                  variant="primary"
                  size="md"
                  icon={Calendar}
                >
                  Schedule a Systems Call with Ariyo
                </Button>
                <a
                  href={CONTACT.linkedin}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-soft-white hover:text-teal transition-colors font-mono"
                >
                  Connect on LinkedIn <ArrowUpRight className="w-4 h-4" />
                </a>
              </div>
            </ScrollReveal>

          </div>

        </div>

      </div>
    </section>
  );
}
