import React from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import SectionHeader from "../components/common/SectionHeader";
import ScrollReveal from "../components/common/ScrollReveal";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import { SERVICES } from "../data/services";
import { CONTACT } from "../data/navigation";
import {
  ShieldCheck,
  CheckCircle2,
  Calendar,
  ArrowRight,
  Database,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";

export default function ServicesPage() {
  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />

      <main className="pt-28 sm:pt-36 pb-24">
        {/* Header Section */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-20 text-center">
          <ScrollReveal delay={0}>
            <div className="inline-flex mb-4">
              <Badge variant="electric" icon={Layers} size="md">
                Consulting Capabilities
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
              Engineered Infrastructure Built for{" "}
              <span className="text-electric-light">Speed, Scale &amp; Reliability.</span>
            </h1>
            <p className="mt-6 text-[16.5px] sm:text-[18px] text-soft-muted max-w-3xl mx-auto leading-relaxed font-normal">
              We specialize across 8 distinct architectural disciplines—building the back-end logic, data pipelines, and intelligent agents that power modern client acquisition and operational efficiency.
            </p>
          </ScrollReveal>
        </section>

        {/* Detailed 8 Services Breakdown */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-24 space-y-12">
          {SERVICES.map((service, index) => {
            const Icon = service.icon;
            const isTeal = service.accent === "teal";

            return (
              <ScrollReveal key={service.id} delay={60}>
                <div
                  id={service.id}
                  className="rounded-3xl border border-deep-blue bg-midnight-dark/95 p-8 sm:p-12 shadow-2xl hover:border-electric/50 transition-all duration-300"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
                    
                    {/* Left Details */}
                    <div className="lg:col-span-7 space-y-5">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-12 h-12 rounded-xl flex items-center justify-center border ${
                            isTeal
                              ? "bg-teal-subtle border-teal/40 text-teal shadow-teal"
                              : "bg-electric-subtle border-electric/40 text-electric-light shadow-highlight"
                          }`}
                        >
                          <Icon className="w-6 h-6" strokeWidth={1.8} />
                        </div>
                        <div>
                          <span className="font-mono text-xs uppercase tracking-wider text-soft-dim font-medium">
                            Capability {String(index + 1).padStart(2, "0")} · {service.tag}
                          </span>
                          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-0.5">
                            {service.title}
                          </h2>
                        </div>
                      </div>

                      <p className="text-[16px] sm:text-[17px] text-soft-muted leading-relaxed font-normal">
                        {service.fullDesc}
                      </p>

                      <div className="pt-2">
                        <Button
                          href={CONTACT.calendlyUrl}
                          target="_blank"
                          variant="primary"
                          size="md"
                          icon={Calendar}
                        >
                          Scope This Capability
                        </Button>
                      </div>
                    </div>

                    {/* Right Deliverables Box */}
                    <div className="lg:col-span-5 bg-midnight rounded-2xl p-6 sm:p-8 border border-deep-blue/80 space-y-4">
                      <h3 className="font-mono text-xs uppercase tracking-wider text-soft-dim font-semibold">
                        Concrete Implementation Scope
                      </h3>

                      <div className="space-y-3">
                        {service.deliverables.map((item, i) => (
                          <div key={i} className="flex items-start gap-3 text-sm sm:text-[14.5px] text-soft-white font-medium">
                            <CheckCircle2
                              className={`w-4 h-4 mt-0.5 shrink-0 ${
                                isTeal ? "text-teal" : "text-electric-light"
                              }`}
                            />
                            <span className="leading-snug">{item}</span>
                          </div>
                        ))}
                      </div>

                      <div className="pt-4 border-t border-deep-blue/70 flex items-center justify-between text-xs font-mono text-soft-dim">
                        <span>Delivery: Fully Tested &amp; Documented</span>
                        <span className="text-teal font-medium">Loom Handover Included</span>
                      </div>
                    </div>

                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </section>

        {/* Global CTA Banner */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <ScrollReveal delay={0}>
            <div className="rounded-3xl border border-deep-blue bg-midnight p-8 sm:p-14 text-center shadow-2xl">
              <h3 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Not sure which service fits your current stage?
              </h3>
              <p className="mt-4 text-[16px] sm:text-[17.5px] text-soft-muted max-w-2xl mx-auto leading-relaxed">
                Book a 30-minute discovery conversation. We'll examine your current tech stack, identify bottlenecks, and map out the cleanest architectural roadmap for your team.
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
                  Quick WhatsApp Chat
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
