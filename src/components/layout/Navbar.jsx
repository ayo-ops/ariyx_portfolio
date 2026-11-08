import React, { useState, useEffect } from "react";
import Logo from "../common/Logo";
import Button from "../common/Button";
import { Link, useRouter } from "../../router";
import { NAV_LINKS, CONTACT } from "../../data/navigation";
import { Menu, X, ArrowUpRight, Calendar } from "lucide-react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { path } = useRouter();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-midnight/95 backdrop-blur-md border-b border-deep-blue/90 py-3.5 shadow-card"
          : "bg-midnight/70 backdrop-blur-sm py-4 sm:py-5 border-b border-deep-blue/40"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="focus:outline-none" aria-label="Ariyx Systems Home">
            <Logo size="md" />
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-7" aria-label="Main Navigation">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.href === "/"
                  ? path === "/"
                  : path.startsWith(link.href);

              return (
                <Link
                  key={link.label}
                  to={link.href}
                  className={`text-[14.5px] font-medium transition-colors duration-150 py-1 relative ${
                    isActive
                      ? "text-white font-semibold"
                      : "text-soft-muted hover:text-white"
                  }`}
                >
                  {link.label}
                  {isActive && (
                    <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-teal rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Desktop Primary CTA */}
          <div className="hidden sm:flex items-center gap-3">
            <Button
              href={CONTACT.calendlyUrl}
              target="_blank"
              variant="primary"
              size="sm"
              icon={Calendar}
            >
              Book a Call
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-soft-white hover:text-white hover:bg-deep-blue/40 border border-deep-blue focus:outline-none cursor-pointer"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-midnight-dark border-b border-deep-blue px-4 pt-4 pb-6 space-y-4 shadow-2xl animate-stage-in">
          <nav className="flex flex-col space-y-1.5">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.href === "/"
                  ? path === "/"
                  : path.startsWith(link.href);

              return (
                <Link
                  key={link.label}
                  to={link.href}
                  onClick={closeMenu}
                  className={`px-3.5 py-2.5 rounded-lg text-base font-medium transition-colors flex items-center justify-between ${
                    isActive
                      ? "bg-deep-blue text-white font-semibold border-l-2 border-teal"
                      : "text-soft-muted hover:text-white hover:bg-deep-blue/40"
                  }`}
                >
                  <span>{link.label}</span>
                  {isActive && <span className="w-1.5 h-1.5 rounded-full bg-teal" />}
                </Link>
              );
            })}
          </nav>

          <div className="pt-3 border-t border-deep-blue flex flex-col gap-2.5">
            <Button
              href={CONTACT.calendlyUrl}
              target="_blank"
              variant="primary"
              size="md"
              className="w-full justify-center"
              icon={Calendar}
              onClick={closeMenu}
            >
              Schedule a Discovery Call
            </Button>
            <Button
              href={CONTACT.whatsappUrl}
              target="_blank"
              variant="outline"
              size="md"
              className="w-full justify-center"
              onClick={closeMenu}
            >
              Quick WhatsApp Chat
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
