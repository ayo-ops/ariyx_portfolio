import React, { useState } from "react";
import SectionHeader from "../common/SectionHeader";
import ScrollReveal from "../common/ScrollReveal";
import { BLUEPRINT_STAGES } from "../../data/systemBlueprint";
import { ArrowRight, CheckCircle2, ChevronRight, Terminal } from "lucide-react";

export default function SystemBlueprintSection() {
  const [selectedStage, setSelectedStage] = useState(BLUEPRINT_STAGES[0]);

  return (
    <section id="systems" className="py-24 sm:py-32 bg-midnight-dark/80 border-y border-deep-blue relative overflow-hidden tech-grid">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal delay={0}>
          <SectionHeader
            badge="End-to-End Pipeline"
            badgeVariant="teal"
            title="The Ariyx Systems"
            highlightText="Architecture Blueprint."
            highlightColor="teal"
            description="A website is only as effective as the underlying data flow. Every project we engineer connects these 7 operational stages into a unified, leak-proof growth engine."
          />
        </ScrollReveal>

        {/* Interactive Desktop Pipeline Grid */}
        <ScrollReveal delay={100}>
          <div className="hidden lg:block mb-10">
            <div className="grid grid-cols-7 gap-3.5 relative">
              {/* Connecting Circuit Trace */}
              <div className="absolute top-1/2 left-6 right-6 h-0.5 bg-deep-blue -translate-y-6 z-0" />

              {BLUEPRINT_STAGES.map((stage) => {
                const Icon = stage.icon;
                const isSelected = selectedStage.id === stage.id;
                const isTeal = stage.color === "teal";

                return (
                  <button
                    key={stage.id}
                    onClick={() => setSelectedStage(stage)}
                    className={`relative z-10 flex flex-col items-center text-center p-4 rounded-xl transition-all duration-300 border cursor-pointer hover:-translate-y-1 ${
                      isSelected
                        ? isTeal
                          ? "bg-midnight border-teal shadow-teal"
                          : "bg-midnight border-electric shadow-highlight"
                        : "bg-midnight/70 border-deep-blue/80 hover:border-white/20 hover:bg-midnight"
                    }`}
                  >
                    {/* Step Badge */}
                    <span className="font-mono text-[11px] text-soft-dim mb-2 uppercase font-medium">
                      Stage {stage.step}
                    </span>

                    {/* Icon Node */}
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center mb-3 transition-colors ${
                        isSelected
                          ? isTeal
                            ? "bg-teal text-midnight-dark shadow-sm"
                            : "bg-electric text-white shadow-sm"
                          : "bg-deep-blue/50 text-soft-white"
                      }`}
                    >
                      <Icon className="w-5 h-5" strokeWidth={1.8} />
                    </div>

                    {/* Node Label */}
                    <span className="text-xs sm:text-[13px] font-bold text-white tracking-tight">
                      {stage.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </ScrollReveal>

        {/* Mobile Stage Selector Tabs */}
        <div className="lg:hidden flex overflow-x-auto gap-2 pb-4 mb-6 scrollbar-none">
          {BLUEPRINT_STAGES.map((stage) => {
            const isSelected = selectedStage.id === stage.id;
            return (
              <button
                key={stage.id}
                onClick={() => setSelectedStage(stage)}
                className={`px-3.5 py-2 rounded-lg text-xs font-mono font-medium shrink-0 border transition-all ${
                  isSelected
                    ? "bg-teal/20 text-teal border-teal shadow-sm"
                    : "bg-midnight text-soft-muted border-deep-blue"
                }`}
              >
                {stage.step}. {stage.label}
              </button>
            );
          })}
        </div>

        {/* Active Stage Detailed Breakdown Panel with Smooth Keyframe Transition */}
        <ScrollReveal delay={180}>
          <div
            key={selectedStage.id}
            className="animate-stage-in rounded-2xl border border-deep-blue bg-midnight p-6 sm:p-10 shadow-2xl relative"
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs px-2.5 py-1 rounded bg-deep-blue/60 border border-deep-blue text-teal font-semibold">
                    STAGE {selectedStage.step} SPECIFICATION
                  </span>
                  <span className="text-soft-dim font-mono text-xs">
                    // {selectedStage.id}.module
                  </span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  {selectedStage.title}
                </h3>

                <p className="text-[16px] sm:text-[17px] text-soft-muted leading-relaxed font-normal">
                  {selectedStage.desc}
                </p>

                {/* Technical Specifications Callout */}
                <div className="pt-2">
                  <div className="p-4 rounded-xl bg-midnight-dark border border-deep-blue/80 flex items-start gap-3">
                    <Terminal className="w-4 h-4 text-teal mt-0.5 shrink-0" />
                    <div className="text-xs sm:text-[13.5px] font-mono text-soft-white leading-relaxed">
                      <span className="text-teal font-bold">Standard Protocol: </span>
                      {selectedStage.spec}
                    </div>
                  </div>
                </div>
              </div>

              {/* Stage Technology Deliverables */}
              <div className="lg:col-span-5 bg-midnight-dark/90 rounded-xl p-6 sm:p-7 border border-deep-blue/80 space-y-4">
                <h4 className="font-mono text-xs uppercase tracking-wider text-soft-dim font-medium">
                  Integrated Technology Stack
                </h4>

                <div className="space-y-3">
                  {selectedStage.tech.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2.5 text-xs sm:text-[13.5px] font-mono text-soft-white"
                    >
                      <CheckCircle2 className="w-4 h-4 text-teal shrink-0" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-4 border-t border-deep-blue/70 flex items-center justify-between text-xs text-soft-dim font-mono">
                  <span>Status: Production Verified</span>
                  <span className="text-teal font-medium">Full API Sync</span>
                </div>
              </div>

            </div>
          </div>
        </ScrollReveal>

      </div>
    </section>
  );
}
