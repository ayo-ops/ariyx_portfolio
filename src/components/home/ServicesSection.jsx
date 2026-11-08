import React from "react";
import SectionHeader from "../common/SectionHeader";
import ScrollReveal from "../common/ScrollReveal";
import { SERVICES } from "../../data/services";
import { Check, ArrowRight } from "lucide-react";
import Button from "../common/Button";
import { CONTACT } from "../../data/navigation";

export default function ServicesSection() {
  return (
    <section id="services" className="py-24 sm:py-32 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal delay={0}>
          <SectionHeader
            badge="Consulting Services"
            badgeVariant="electric"
            title="Architectural Capabilities Built for"
            highlightText="Predictable Operations."
            highlightColor="electric"
            description="We don't offer generic templates or superficial design tweaks. We engineer the underlying CRM, automation, and AI infrastructure that powers your entire client acquisition and delivery lifecycle."
          />
        </ScrollReveal>

        {/* 8-Pillar Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {SERVICES.map((service, index) => {
            const Icon = service.icon;
            const isTeal = service.accent === "teal";

            return (
              <ScrollReveal key={service.id} delay={index * 60}>
                <div
                  className="group h-full rounded-2xl border border-deep-blue bg-midnight/85 p-6 sm:p-7 flex flex-col justify-between hover:border-electric/70 hover:bg-midnight-light/60 transition-all duration-300 shadow-card hover:shadow-card-hover hover:-translate-y-1.5"
                >
                  <div>
                    {/* Top bar with Icon and Category Tag */}
                    <div className="flex items-center justify-between mb-5">
                      <div
                        className={`w-12 h-12 rounded-xl border flex items-center justify-center transition-transform group-hover:scale-110 duration-200 ${
                          isTeal
                            ? "bg-teal-subtle border-teal/40 text-teal shadow-teal"
                            : "bg-electric-subtle border-electric/40 text-electric-light shadow-highlight"
                        }`}
                      >
                        <Icon className="w-6 h-6" strokeWidth={1.8} />
                      </div>
                      <span className="font-mono text-[11px] uppercase tracking-wider text-soft-dim px-2.5 py-1 rounded-md bg-deep-blue/40 border border-deep-blue font-medium">
                        {service.tag}
                      </span>
                    </div>

                    {/* Service Title */}
                    <h3 className="text-xl font-bold text-white tracking-tight mb-3 group-hover:text-electric-light transition-colors leading-snug">
                      {service.title}
                    </h3>

                    {/* Short Description (14.5px - 15px readable text) */}
                    <p className="text-[14.5px] text-soft-muted leading-relaxed mb-6 font-normal">
                      {service.shortDesc}
                    </p>

                    {/* Concrete Deliverables List */}
                    <div className="space-y-2.5 border-t border-deep-blue/70 pt-4 mb-6">
                      {service.deliverables.map((item, i) => (
                        <div key={i} className="flex items-start gap-2 text-[13px] sm:text-[13.5px] text-soft-white">
                          <Check
                            className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                              isTeal ? "text-teal" : "text-electric-light"
                            }`}
                          />
                          <span className="leading-snug">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Card Action Link */}
                  <div className="pt-2">
                    <a
                      href={CONTACT.calendlyUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-soft-white group-hover:text-teal transition-colors"
                    >
                      <span>Discuss Architecture</span>
                      <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                    </a>
                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </div>

        {/* Section Bottom Banner */}
        <ScrollReveal delay={200}>
          <div className="mt-16 rounded-2xl border border-deep-blue bg-midnight-dark p-8 sm:p-10 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl">
            <div className="space-y-2 text-center md:text-left">
              <h4 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Need a bespoke combination of these systems?
              </h4>
              <p className="text-[15px] sm:text-[16px] text-soft-muted max-w-xl leading-relaxed">
                Most clients require an interconnected setup (e.g. GoHighLevel CRM + n8n Webhook bridges + Voice AI). We map the entire data flow before building.
              </p>
            </div>
            <Button
              href={CONTACT.calendlyUrl}
              target="_blank"
              variant="teal"
              size="md"
            >
              Request Systems Assessment
            </Button>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
