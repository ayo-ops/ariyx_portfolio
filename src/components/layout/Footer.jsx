import React from "react";
import Logo from "../common/Logo";
import { Link } from "../../router";
import { CONTACT, FOOTER_LINKS } from "../../data/navigation";
import {
  Mail,
  MessageSquare,
  Link as LinkIcon,
  Briefcase,
  ArrowUpRight,
  Calendar,
} from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-midnight-dark border-t border-deep-blue relative pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 lg:gap-8 pb-12 border-b border-deep-blue/70">
          
          {/* Brand Info */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/">
              <Logo size="lg" />
            </Link>
            <p className="text-[14.5px] sm:text-[15px] text-soft-muted max-w-sm leading-relaxed font-normal">
              CRM, Automation and AI Systems Consultancy. We engineer reliable data
              pipelines, autonomous workflows, and communication agents for
              growing businesses.
            </p>
            <div className="pt-2">
              <a
                href={CONTACT.calendlyUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 text-sm font-semibold text-teal hover:text-teal-light transition-colors"
              >
                <Calendar className="w-4 h-4" /> Schedule a 30-Min Systems Audit
                <ArrowUpRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* Consulting Capabilities */}
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-soft-dim mb-4 font-semibold">
              Capabilities
            </h3>
            <ul className="space-y-2.5 text-[14px]">
              {FOOTER_LINKS.services.map((item) => (
                <li key={item.label}>
                  <Link
                    to={item.href}
                    className="text-soft-muted hover:text-white transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Solutions & Problems Solved */}
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-soft-dim mb-4 font-semibold">
              Solutions
            </h3>
            <ul className="space-y-2.5 text-[14px]">
              {FOOTER_LINKS.solutions.map((item) => (
                <li key={item.label}>
                  <Link
                    to={item.href}
                    className="text-soft-muted hover:text-white transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Direct Channels & Company */}
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-soft-dim mb-4 font-semibold">
              Connect
            </h3>
            <ul className="space-y-3 text-[14px]">
              <li>
                <a
                  href={`mailto:${CONTACT.email}`}
                  className="flex items-center gap-2 text-soft-muted hover:text-white transition-colors"
                >
                  <Mail className="w-4 h-4 text-electric" />
                  <span className="truncate">{CONTACT.email}</span>
                </a>
              </li>
              <li>
                <a
                  href={CONTACT.whatsappUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 text-soft-muted hover:text-white transition-colors"
                >
                  <MessageSquare className="w-4 h-4 text-teal" />
                  <span>WhatsApp Chat</span>
                </a>
              </li>
              <li>
                <a
                  href={CONTACT.linkedin}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 text-soft-muted hover:text-white transition-colors"
                >
                  <LinkIcon className="w-4 h-4 text-electric" />
                  <span>LinkedIn Profile</span>
                </a>
              </li>
              <li>
                <a
                  href={CONTACT.upwork}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 text-soft-muted hover:text-white transition-colors"
                >
                  <Briefcase className="w-4 h-4 text-teal" />
                  <span>Upwork Verified</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-soft-dim">
          <p>© {new Date().getFullYear()} Ariyx Systems. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link to="/about" className="hover:text-soft-white transition-colors">
              About
            </Link>
            <Link to="/services" className="hover:text-soft-white transition-colors">
              Services
            </Link>
            <Link to="/solutions" className="hover:text-soft-white transition-colors">
              Solutions
            </Link>
            <Link to="/portfolio" className="hover:text-soft-white transition-colors">
              Portfolio
            </Link>
            <Link to="/insights" className="hover:text-soft-white transition-colors">
              Insights
            </Link>
            <Link to="/contact" className="hover:text-soft-white transition-colors">
              Contact
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
