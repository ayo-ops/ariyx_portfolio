import React from "react";

export default function Badge({
  children,
  variant = "electric",
  icon: Icon,
  className = "",
  size = "md",
}) {
  const variants = {
    electric: "border-electric/30 bg-electric-subtle text-electric-light",
    teal: "border-teal/30 bg-teal-subtle text-teal-light",
    neutral: "border-white/10 bg-white/[0.04] text-soft-white/70",
  };

  const sizes = {
    sm: "px-2.5 py-1 text-xs gap-1.5",
    md: "px-3.5 py-1.5 text-xs sm:text-sm gap-2",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border font-mono tracking-wider uppercase font-medium ${
        variants[variant] || variants.electric
      } ${sizes[size] || sizes.md} ${className}`}
    >
      {Icon && <Icon className="w-3.5 h-3.5 shrink-0" />}
      {children}
    </span>
  );
}
