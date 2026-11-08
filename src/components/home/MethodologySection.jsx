import React from "react";
import SectionHeader from "../common/SectionHeader";
import ScrollReveal from "../common/ScrollReveal";
import { METHODOLOGY_STEPS } from "../../data/methodology";
import { CheckCircle2, ArrowRight } from "lucide-react";

export default function MethodologySection() {
  return (
    <section id="methodology" className="py-24 sm:py-32 bg-midnight-dark border-y border-deep-blue relative tech-dots">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal delay={0}>
          <SectionHeader
            badge="Delivery Framework"
            badgeVariant="teal"
            title="A Structured, Repeatable"
            highlightText="Consulting Methodology."
            highlightColor="teal"
            description="We take the guesswork out of systems implementation. Every engagement follows a disciplined four-stage engineering roadmap designed to prevent scope creep and ensure reliable delivery."
          />
        </ScrollReveal>

        {/* 4-Step Methodology Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
          {METHODOLOGY_STEPS.map((step, index) => (
            <ScrollReveal key={step.step} delay={index * 80}>
              <div
                className="h-full rounded-2xl border border-deep-blue bg-midnight p-6 sm:p-7 flex flex-col justify-between hover:border-teal/50 hover:-translate-y-1.5 transition-all duration-300 shadow-card"
              >
                <div>
                  {/* Step Header */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-2xl sm:text-3xl font-extrabold text-teal">
                      {step.step}
                    </span>
                    <span className="font-mono text-xs uppercase tracking-wider text-soft-dim px-2.5 py-1 rounded bg-deep-blue/40 border border-deep-blue font-medium">
                      {step.phase}
                    </span>
                  </div>

                  {/* Step Title */}
                  <h3 className="text-xl font-bold text-white tracking-tight mb-3 leading-snug">
                    {step.title}
                  </h3>

                  {/* Step Description */}
                  <p className="text-[14.5px] sm:text-[15px] text-soft-muted leading-relaxed mb-6 font-normal">
                    {step.description}
                  </p>
                </div>

                {/* Deliverables Box */}
                <div className="pt-4 border-t border-deep-blue/70 space-y-2.5">
                  <span className="font-mono text-xs uppercase tracking-wider text-soft-dim block mb-1 font-medium">
                    Key Output:
                  </span>
                  {step.deliverables.map((item, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs sm:text-[13px] text-soft-white font-medium">
                      <CheckCircle2 className="w-4 h-4 text-teal shrink-0 mt-0.5" />
                      <span className="leading-snug">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
