import React, { useState, useEffect } from "react";
import SectionHeader from "../common/SectionHeader";
import ScrollReveal from "../common/ScrollReveal";
import { TESTIMONIALS } from "../../data/testimonials";
import { Star, ChevronLeft, ChevronRight, Quote } from "lucide-react";

export default function TestimonialsSection() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-advance every 6 seconds unless user is hovering
  useEffect(() => {
    if (isPaused) return;
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % TESTIMONIALS.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [isPaused]);

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + TESTIMONIALS.length) % TESTIMONIALS.length);
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % TESTIMONIALS.length);
  };

  const activeReview = TESTIMONIALS[currentIndex];

  return (
    <section id="reviews" className="py-24 sm:py-32 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <ScrollReveal delay={0}>
          <SectionHeader
            badge="Verified Client Reviews"
            badgeVariant="electric"
            title="Direct Feedback from"
            highlightText="Businesses We've Supported."
            highlightColor="electric"
            description="Real testimonials from business owners, founders, and operators who rely on our CRM, automation, and workflow setups daily."
            align="center"
          />
        </ScrollReveal>

        {/* Featured Testimonial Card */}
        <ScrollReveal delay={120}>
          <div
            className="max-w-4xl mx-auto"
            onMouseEnter={() => setIsPaused(true)}
            onMouseLeave={() => setIsPaused(false)}
          >
            <div
              key={activeReview.id}
              className="animate-stage-in rounded-3xl border border-deep-blue bg-midnight/90 p-8 sm:p-12 shadow-2xl relative"
            >
              
              {/* Top Bar: Highlight badge & 5 stars */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                <span className="font-mono text-xs sm:text-[13px] px-3.5 py-1.5 rounded-full bg-deep-blue/60 border border-deep-blue text-teal uppercase tracking-wider font-semibold w-fit">
                  {activeReview.highlight}
                </span>

                <div className="flex items-center gap-1.5">
                  {Array.from({ length: activeReview.rating }).map((_, i) => (
                    <Star
                      key={i}
                      className="w-4 h-4 sm:w-5 sm:h-5 fill-amber-400 text-amber-400"
                    />
                  ))}
                  <span className="ml-2 font-mono text-xs sm:text-sm text-soft-dim font-bold">5.0 / 5.0</span>
                </div>
              </div>

              {/* Testimonial Quote */}
              <blockquote className="text-xl sm:text-2xl lg:text-[23px] font-medium text-white leading-relaxed mb-8">
                &ldquo;{activeReview.review}&rdquo;
              </blockquote>

              {/* Client Signature & Navigation Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pt-6 border-t border-deep-blue/80">
                <div>
                  <div className="text-lg sm:text-xl font-bold text-white tracking-tight">
                    {activeReview.name}
                  </div>
                  <div className="text-xs sm:text-sm font-mono text-soft-dim mt-0.5">
                    {activeReview.business}
                  </div>
                </div>

                {/* Prev / Next Buttons */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={handlePrev}
                    className="w-11 h-11 rounded-full border border-deep-blue bg-midnight-dark text-soft-white hover:text-white hover:border-electric flex items-center justify-center transition-all cursor-pointer active:scale-95"
                    aria-label="Previous testimonial"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  
                  <span className="font-mono text-xs sm:text-sm text-soft-dim min-w-[55px] text-center font-medium">
                    {String(currentIndex + 1).padStart(2, "0")} / {String(TESTIMONIALS.length).padStart(2, "0")}
                  </span>

                  <button
                    onClick={handleNext}
                    className="w-11 h-11 rounded-full border border-deep-blue bg-midnight-dark text-soft-white hover:text-white hover:border-electric flex items-center justify-center transition-all cursor-pointer active:scale-95"
                    aria-label="Next testimonial"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>

            </div>

            {/* Quick Pagination Dots */}
            <div className="flex justify-center items-center gap-2 mt-8">
              {TESTIMONIALS.map((t, idx) => (
                <button
                  key={t.id}
                  onClick={() => setCurrentIndex(idx)}
                  className={`h-2 rounded-full transition-all duration-300 cursor-pointer ${
                    idx === currentIndex
                      ? "w-8 bg-teal shadow-teal"
                      : "w-2 bg-deep-blue hover:bg-white/40"
                  }`}
                  aria-label={`Go to testimonial ${idx + 1}`}
                />
              ))}
            </div>
          </div>
        </ScrollReveal>

      </div>
    </section>
  );
}
