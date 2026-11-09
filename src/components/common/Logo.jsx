import React from "react";

export default function Logo({ className = "", showWordmark = true, size = "md" }) {
  const iconSizes = {
    sm: "w-8 h-8",
    md: "w-9 h-9 sm:w-10 sm:h-10",
    lg: "w-11 h-11 sm:w-12 sm:h-12",
  };

  const textSizes = {
    sm: "text-[15px] tracking-[0.18em]",
    md: "text-[17px] sm:text-[18px] tracking-[0.2em]",
    lg: "text-xl sm:text-[22px] tracking-[0.22em]",
  };

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Official Ariyx Systems Logo — exact asset from favicon */}
      <img
        src="/favicon.svg"
        alt="Ariyx Systems Logo"
        width="48"
        height="48"
        className={`${iconSizes[size] || iconSizes.md} shrink-0 object-contain rounded-xl shadow-sm`}
      />

      {/* Clean ARIYX SYSTEMS Wordmark */}
      {showWordmark && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center gap-1.5">
            <span className={`font-sans font-extrabold text-white uppercase ${textSizes[size] || textSizes.md}`}>
              ARIYX
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-teal shrink-0" />
            <span className={`font-sans font-semibold text-soft-white/70 uppercase ${textSizes[size] || textSizes.md}`}>
              SYSTEMS
            </span>
          </div>
          <span className="font-mono text-[9px] sm:text-[9.5px] tracking-[0.25em] text-soft-white/40 uppercase mt-0.5">
            Consultancy
          </span>
        </div>
      )}
    </div>
  );
}
