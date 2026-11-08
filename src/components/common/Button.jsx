import React from "react";
import { ArrowUpRight } from "lucide-react";
import { Link } from "../../router";

export default function Button({
  children,
  variant = "primary",
  size = "md",
  href,
  onClick,
  target,
  rel,
  className = "",
  icon: Icon,
  showArrow = false,
  ...props
}) {
  const baseClasses =
    "inline-flex items-center justify-center font-sans font-medium rounded-full transition-all duration-200 cursor-pointer select-none active:scale-[0.98]";

  const variants = {
    primary:
      "bg-electric text-white hover:bg-electric-light shadow-sm hover:shadow-highlight",
    secondary:
      "bg-deep-blue text-soft-white border border-deep-blue/80 hover:bg-deep-hover hover:border-electric/40",
    teal:
      "bg-teal text-midnight-dark font-semibold hover:bg-teal-light shadow-sm hover:shadow-teal",
    outline:
      "bg-transparent border border-white/15 text-soft-white hover:border-electric/50 hover:bg-white/[0.04]",
    ghost:
      "bg-transparent text-soft-white/80 hover:text-white hover:bg-white/[0.06]",
  };

  const sizes = {
    sm: "px-4 py-2 text-sm gap-2",
    md: "px-6 py-3 text-sm sm:text-base gap-2.5",
    lg: "px-7 py-3.5 text-base sm:text-lg gap-3",
  };

  const combinedClasses = `${baseClasses} ${variants[variant] || variants.primary} ${
    sizes[size] || sizes.md
  } ${className}`;

  const content = (
    <>
      {Icon && <Icon className="w-4 h-4 shrink-0" />}
      <span>{children}</span>
      {showArrow && <ArrowUpRight className="w-4 h-4 shrink-0 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />}
    </>
  );

  if (href) {
    if (href.startsWith("/") && !href.startsWith("//")) {
      return (
        <Link
          to={href}
          className={`group ${combinedClasses}`}
          onClick={onClick}
          {...props}
        >
          {content}
        </Link>
      );
    }

    return (
      <a
        href={href}
        target={target}
        rel={target === "_blank" ? "noreferrer noopener" : rel}
        className={`group ${combinedClasses}`}
        onClick={onClick}
        {...props}
      >
        {content}
      </a>
    );
  }

  return (
    <button onClick={onClick} className={`group ${combinedClasses}`} {...props}>
      {content}
    </button>
  );
}
