import React from "react";
import Button from "../common/Button";
import ScrollReveal from "../common/ScrollReveal";
import { CONTACT } from "../../data/navigation";
import { Calendar, MessageSquare, Mail, ArrowRight, ShieldCheck } from "lucide-react";

export default function ConversionSection() {
  return (
    <section className="py-24 sm:py-32 relative tech-grid border-t border-deep-blue">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <ScrollReveal delay={0}>
          <div className="rounded-3xl border border-deep-blue bg-midnight-dark/95 p-8 sm:p-14 text-center shadow-2xl relative overflow-hidden">
            
            {/* Subtle circuit corner accent */}
            <div className="absolute top-0 right-0 w-32 h-32 border-t-2 border-r-2 border-teal/20 rounded-tr-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-32 h-32 border-b-2 border-l-2 border-electric/20 rounded-bl-3xl pointer-events-none" />

            {/* Eyebrow */}
            <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.22em] text-teal mb-4 font-medium">
              <ShieldCheck className="w-4 h-4" />
              Direct Systems Consultation
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-[46px] font-extrabold text-white tracking-tight leading-tight max-w-2xl mx-auto">
              Ready to Upgrade Your Business Infrastructure?
            </h2>

            <p className="mt-5 text-[16.5px] sm:text-[18px] text-soft-muted max-w-2xl mx-auto leading-relaxed font-normal">
              Tell us where your lead flow is stalling or which manual tasks are consuming your team's hours. We'll help map the most pragmatic CRM, automation, and AI architecture to fix it.
            </p>

            {/* Action Buttons */}
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button
                href={CONTACT.calendlyUrl}
                target="_blank"
                variant="primary"
                size="lg"
                icon={Calendar}
              >
                Schedule a 30-Min Call
              </Button>
              <Button
                href={CONTACT.whatsappUrl}
                target="_blank"
                variant="outline"
                size="lg"
                icon={MessageSquare}
              >
                Direct WhatsApp Chat
              </Button>
            </div>

            {/* Email fallback */}
            <div className="mt-6 text-xs sm:text-sm font-mono text-soft-dim">
              Prefer direct email? Reach out to{" "}
              <a
                href={`mailto:${CONTACT.email}`}
                className="text-soft-white hover:text-teal underline underline-offset-4 transition-colors font-medium"
              >
                {CONTACT.email}
              </a>
            </div>

          </div>
        </ScrollReveal>

      </div>
    </section>
  );
}
