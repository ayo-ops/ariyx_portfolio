import React from "react";

export default function Logo({ className = "h-8", showWordmark = true, size = "md" }) {
  const iconSizes = {
    sm: "w-7 h-7",
    md: "w-9 h-9",
    lg: "w-11 h-11",
  };

  const textSizes = {
    sm: "text-base tracking-[0.18em]",
    md: "text-lg tracking-[0.2em]",
    lg: "text-xl tracking-[0.22em]",
  };

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Abstract Circuit "A" Symbol */}
      <div className={`relative shrink-0 ${iconSizes[size] || iconSizes.md} rounded-xl bg-midnight border border-deep-blue flex items-center justify-center p-1.5 shadow-sm`}>
        <svg
          viewBox="0 0 36 36"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Circuit background traces */}
          <path
            d="M6 30L18 6L30 30"
            stroke="#243B60"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Active circuit path */}
          <path
            d="M6 30L18 6L30 30"
            stroke="url(#circuitGrad)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Crossbar with circuit node */}
          <line
            x1="11"
            y1="22"
            x2="25"
            y2="22"
            stroke="#21C7B7"
            strokeWidth="2"
            strokeLinecap="round"
          />
          {/* Central circuit micro-node */}
          <circle cx="18" cy="22" r="2" fill="#FFFFFF" />
          {/* Apex node */}
          <circle cx="18" cy="6" r="2.2" fill="#21C7B7" />
          {/* Base termination nodes */}
          <circle cx="6" cy="30" r="1.8" fill="#3B82F6" />
          <circle cx="30" cy="30" r="1.8" fill="#3B82F6" />

          <defs>
            <linearGradient id="circuitGrad" x1="6" y1="6" x2="30" y2="30" gradientUnits="userSpaceOnUse">
              <stop stopColor="#3B82F6" />
              <stop offset="1" stopColor="#21C7B7" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Clean ARIYX SYSTEMS Wordmark */}
      {showWordmark && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center gap-1.5">
            <span className={`font-sans font-bold text-white uppercase ${textSizes[size] || textSizes.md}`}>
              ARIYX
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-teal shrink-0" />
            <span className={`font-sans font-semibold text-soft-white/60 uppercase ${textSizes[size] || textSizes.md}`}>
              SYSTEMS
            </span>
          </div>
          <span className="font-mono text-[9px] tracking-[0.25em] text-soft-white/40 uppercase mt-0.5">
            Consultancy
          </span>
        </div>
      )}
    </div>
  );
}
