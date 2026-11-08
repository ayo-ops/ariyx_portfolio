import React, { useState } from "react";
import { VIDEO_TESTIMONIAL } from "../../data/testimonials";
import { PLATFORMS } from "../../data/platforms";
import VideoModal from "./VideoModal";
import ScrollReveal from "../common/ScrollReveal";
import { Play, CheckCircle2, ShieldCheck, ArrowRight } from "lucide-react";

export default function VerifiedProofSection() {
  const [isVideoOpen, setIsVideoOpen] = useState(false);

  return (
    <>
      <section className="relative border-y border-deep-blue/80 bg-midnight-dark py-12 lg:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Main Card: Patty Jackson Video Feature */}
          <ScrollReveal delay={0}>
            <div className="rounded-2xl border border-deep-blue bg-midnight/80 p-6 sm:p-8 lg:p-10 shadow-card hover:border-teal/40 transition-colors">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
                
                {/* Video Thumbnail Trigger with gentle zoom */}
                <div className="lg:col-span-5">
                  <div
                    onClick={() => setIsVideoOpen(true)}
                    className="group relative aspect-video rounded-xl overflow-hidden border border-deep-blue bg-midnight cursor-pointer hover:border-teal/60 transition-all duration-300 shadow-md"
                  >
                    <img
                      src={VIDEO_TESTIMONIAL.poster}
                      alt={`${VIDEO_TESTIMONIAL.client} Video Testimonial`}
                      className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-[1.04] transition-all duration-500 ease-out"
                    />
                    
                    {/* Subtle overlay */}
                    <div className="absolute inset-0 bg-midnight/30 group-hover:bg-midnight/10 transition-colors" />

                    {/* Play Button Indicator */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-14 h-14 rounded-full bg-teal text-midnight-dark flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200">
                        <Play className="w-6 h-6 ml-1 fill-current" />
                      </div>
                    </div>

                    {/* Video Badge */}
                    <div className="absolute top-3 left-3 px-3 py-1 rounded-md bg-midnight/90 backdrop-blur-sm border border-white/10 text-xs font-mono text-soft-white flex items-center gap-1.5 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
                      CLIENT INTERVIEW
                    </div>
                  </div>
                </div>

                {/* Video Testimonial Description & Impact */}
                <div className="lg:col-span-7 space-y-4">
                  <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-teal font-medium">
                    <ShieldCheck className="w-4 h-4" />
                    Verified Systems Implementation
                  </div>

                  <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
                    &ldquo;Transformed how our coaching certification captures and follows up with leads.&rdquo;
                  </h3>

                  <p className="text-[16px] sm:text-[17px] text-soft-muted leading-relaxed font-normal">
                    {VIDEO_TESTIMONIAL.caption}
                  </p>

                  <div className="pt-3 flex flex-wrap items-center justify-between gap-4 border-t border-deep-blue/80">
                    <div>
                      <div className="font-bold text-white text-base">
                        {VIDEO_TESTIMONIAL.client}
                      </div>
                      <div className="text-xs sm:text-[13px] text-soft-dim font-mono mt-0.5">
                        Founder · {VIDEO_TESTIMONIAL.business} ({VIDEO_TESTIMONIAL.niche})
                      </div>
                    </div>

                    <button
                      onClick={() => setIsVideoOpen(true)}
                      className="inline-flex items-center gap-2 text-sm font-bold text-teal hover:text-teal-light font-mono transition-colors cursor-pointer"
                    >
                      Watch Case Breakdown <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>

              </div>
            </div>
          </ScrollReveal>

          {/* Connected Technical Ecosystem Ticker */}
          <ScrollReveal delay={120}>
            <div className="mt-12 pt-8 border-t border-deep-blue/60">
              <div className="text-center mb-6">
                <span className="font-mono text-xs uppercase tracking-[0.22em] text-soft-dim font-medium">
                  Integrated Across Modern Technology &amp; CRM Stacks
                </span>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
                {PLATFORMS.map((platform) => (
                  <div
                    key={platform.name}
                    className="px-4 py-2.5 rounded-xl bg-midnight border border-deep-blue/80 hover:border-electric/50 transition-colors flex items-center gap-2.5 shadow-sm"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-electric-light shrink-0" />
                    <span className="font-mono text-xs sm:text-[13.5px] font-semibold text-soft-white">
                      {platform.name}
                    </span>
                    <span className="text-xs text-soft-dim hidden md:inline font-mono">
                      · {platform.role}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </ScrollReveal>

        </div>
      </section>

      {/* Video Modal */}
      <VideoModal
        isOpen={isVideoOpen}
        onClose={() => setIsVideoOpen(false)}
        videoSrc={VIDEO_TESTIMONIAL.src}
        poster={VIDEO_TESTIMONIAL.poster}
        title={`${VIDEO_TESTIMONIAL.client} (${VIDEO_TESTIMONIAL.business})`}
      />
    </>
  );
}
