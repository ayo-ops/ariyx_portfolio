import React from "react";

export default function SectionHeader({
  badge,
  badgeIcon,
  badgeVariant = "electric",
  title,
  highlightText,
  highlightColor = "teal", // "teal" | "electric"
  description,
  align = "left", // "left" | "center"
  className = "",
}) {
  const isCentered = align === "center";

  const highlightClasses = {
    teal: "text-teal font-semibold",
    electric: "text-electric-light font-semibold",
  };

  return (
    <div
      className={`mb-12 sm:mb-16 ${
        isCentered ? "text-center max-w-3xl mx-auto" : "max-w-2xl"
      } ${className}`}
    >
      {badge && (
        <div
          className={`flex items-center gap-2.5 mb-4 ${
            isCentered ? "justify-center" : "justify-start"
          }`}
        >
          <span className="inline-flex items-center gap-2 font-mono text-xs sm:text-[13px] tracking-[0.22em] uppercase text-soft-dim font-medium">
            <span
              className={`w-2 h-2 rounded-full ${
                badgeVariant === "teal" ? "bg-teal shadow-teal" : "bg-electric shadow-highlight"
              }`}
            />
            {badge}
          </span>
          <span className="h-px w-10 bg-deep-blue" />
        </div>
      )}

      <h2 className="text-3xl sm:text-4xl lg:text-[42px] xl:text-[46px] font-extrabold tracking-tight text-white leading-[1.16]">
        {title}{" "}
        {highlightText && (
          <span className={highlightClasses[highlightColor] || highlightClasses.teal}>
            {highlightText}
          </span>
        )}
      </h2>

      {description && (
        <p className="mt-4 text-[16px] sm:text-[17px] text-soft-muted leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
}
