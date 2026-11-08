import React, { useState } from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import SectionHeader from "../components/common/SectionHeader";
import ScrollReveal from "../components/common/ScrollReveal";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import { CONTACT } from "../data/navigation";
import { APPS_SCRIPT_ENDPOINT } from "../data/api";
import {
  Mail,
  MessageSquare,
  Calendar,
  Briefcase,
  CheckCircle2,
  ShieldCheck,
  Send,
  AlertCircle,
  Clock,
  Link as LinkIcon,
  Loader2,
} from "lucide-react";

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    company: "",
    serviceNeed: "CRM Implementation & Management",
    timeline: "Within 2–4 weeks",
    message: "",
  });

  const [honeypot, setHoneypot] = useState("");
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = "Please provide your full name.";
    } else if (formData.name.trim().length > 100) {
      newErrors.name = "Name must be 100 characters or less.";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Please provide your business email.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = "Please enter a valid email address.";
    } else if (formData.email.trim().length > 150) {
      newErrors.email = "Email must be 150 characters or less.";
    }

    if (formData.phone && formData.phone.trim().length > 50) {
      newErrors.phone = "Phone number must be 50 characters or less.";
    }

    if (formData.company && formData.company.trim().length > 150) {
      newErrors.company = "Company name must be 150 characters or less.";
    }

    if (!formData.message.trim()) {
      newErrors.message = "Please describe what system or bottleneck you're looking to solve.";
    } else if (formData.message.trim().length > 3000) {
      newErrors.message = "Message must be 3,000 characters or less.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError("");

    // Spam honeypot check: If filled, silently abort without pinging Apps Script
    if (honeypot.trim() !== "") {
      setIsSubmitting(true);
      setTimeout(() => {
        setIsSubmitting(false);
        setIsSubmitted(true);
      }, 700);
      return;
    }

    if (!validate()) return;

    // Client-side cooldown rate-limit (60s cooldown per browser)
    const COOLDOWN_MS = 60000;
    const lastSent = localStorage.getItem("ariyx_last_contact_ts");
    if (lastSent) {
      const elapsed = Date.now() - parseInt(lastSent, 10);
      if (elapsed < COOLDOWN_MS) {
        const remaining = Math.ceil((COOLDOWN_MS - elapsed) / 1000);
        setServerError(
          `A submission was recently received. Please wait ${remaining}s before submitting again or reach out on WhatsApp.`
        );
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const payload = {
        action: "contact",
        name: formData.name.trim().slice(0, 100),
        email: formData.email.trim().slice(0, 150),
        phone: formData.phone.trim().slice(0, 50),
        company: formData.company.trim().slice(0, 150),
        system: formData.serviceNeed,
        timeline: formData.timeline,
        challenge: formData.message.trim().slice(0, 3000),
      };

      const response = await fetch(APPS_SCRIPT_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "text/plain;charset=utf-8",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result && result.success === true) {
        try {
          localStorage.setItem("ariyx_last_contact_ts", Date.now().toString());
        } catch (_) {}
        setIsSubmitted(true);
      } else {
        setServerError(
          result?.message ||
            "Unable to process your inquiry. Please try again or reach out directly via WhatsApp."
        );
      }
    } catch (err) {
      console.error("Submission error:", err);
      setServerError(
        "Network connection issue. Please check your internet connection or message us directly on WhatsApp or Email."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: "",
      email: "",
      phone: "",
      company: "",
      serviceNeed: "CRM Implementation & Management",
      timeline: "Within 2–4 weeks",
      message: "",
    });
    setHoneypot("");
    setIsSubmitted(false);
    setServerError("");
    setErrors({});
  };

  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />

      <main className="pt-28 sm:pt-36 pb-24">
        {/* Header Section */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16 text-center">
          <ScrollReveal delay={0}>
            <div className="inline-flex mb-4">
              <Badge variant="teal" icon={MessageSquare} size="md">
                Direct Consultation &amp; Inquiry
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
              Let's Discuss Your{" "}
              <span className="text-teal">Systems Architecture.</span>
            </h1>
            <p className="mt-6 text-[16.5px] sm:text-[18px] text-soft-muted max-w-2xl mx-auto leading-relaxed font-normal">
              Whether you need to overhaul a disorganized CRM, deploy Voice AI agents, or automate complex business workflows, we are ready to map out your architecture.
            </p>
          </ScrollReveal>
        </section>

        {/* Contact Form & Direct Channels Grid */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-20">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-start">
            
            {/* Left Column: Direct Communication Channels */}
            <div className="lg:col-span-5 space-y-8">
              <ScrollReveal delay={80}>
                {/* Instant Calendly Booking Card */}
                <div className="rounded-2xl border border-deep-blue bg-midnight-dark p-7 shadow-xl space-y-4">
                  <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-teal font-semibold">
                    <Calendar className="w-4 h-4" /> Immediate Calendar Lock
                  </div>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Schedule a 30-Minute Architecture Call
                  </h3>
                  <p className="text-[14.5px] sm:text-[15px] text-soft-muted leading-relaxed font-normal">
                    Pick a direct slot on Ariyo's calendar. We'll review your current processes, software stack, and implementation timeline.
                  </p>
                  <div className="pt-2">
                    <Button
                      href={CONTACT.calendlyUrl}
                      target="_blank"
                      variant="primary"
                      size="md"
                      icon={Calendar}
                      className="w-full justify-center"
                    >
                      Open Live Calendar
                    </Button>
                  </div>
                </div>
              </ScrollReveal>

              <ScrollReveal delay={140}>
                {/* Direct Channels List */}
                <div className="rounded-2xl border border-deep-blue bg-midnight-dark p-7 shadow-xl space-y-5">
                  <h4 className="font-mono text-xs uppercase tracking-wider text-soft-dim font-semibold">
                    Direct Channels
                  </h4>

                  <ul className="space-y-4 text-sm font-mono">
                    <li>
                      <a
                        href={`mailto:${CONTACT.email}`}
                        className="flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/80 hover:border-electric transition-colors"
                      >
                        <Mail className="w-5 h-5 text-electric shrink-0 mt-0.5" />
                        <div>
                          <div className="text-xs text-soft-dim">Direct Email</div>
                          <div className="text-sm text-soft-white font-medium">{CONTACT.email}</div>
                        </div>
                      </a>
                    </li>

                    <li>
                      <a
                        href={CONTACT.whatsappUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/80 hover:border-teal transition-colors"
                      >
                        <MessageSquare className="w-5 h-5 text-teal shrink-0 mt-0.5" />
                        <div>
                          <div className="text-xs text-soft-dim">WhatsApp Priority</div>
                          <div className="text-sm text-soft-white font-medium">+234 915 258 1764</div>
                        </div>
                      </a>
                    </li>

                    <li>
                      <a
                        href={CONTACT.linkedin}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/80 hover:border-electric transition-colors"
                      >
                        <LinkIcon className="w-5 h-5 text-electric shrink-0 mt-0.5" />
                        <div>
                          <div className="text-xs text-soft-dim">LinkedIn</div>
                          <div className="text-sm text-soft-white font-medium">Ariyo Emmanuel</div>
                        </div>
                      </a>
                    </li>

                    <li>
                      <a
                        href={CONTACT.upwork}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-start gap-3 p-3 rounded-xl bg-midnight border border-deep-blue/80 hover:border-teal transition-colors"
                      >
                        <Briefcase className="w-5 h-5 text-teal shrink-0 mt-0.5" />
                        <div>
                          <div className="text-xs text-soft-dim">Upwork</div>
                          <div className="text-sm text-soft-white font-medium">Verified Profile</div>
                        </div>
                      </a>
                    </li>
                  </ul>
                </div>
              </ScrollReveal>
            </div>

            {/* Right Column: Functional Interactive Contact Form */}
            <div className="lg:col-span-7">
              <ScrollReveal delay={120}>
                <div className="rounded-3xl border border-deep-blue bg-midnight-dark/95 p-8 sm:p-12 shadow-2xl">
                  
                  {isSubmitted ? (
                    <div className="py-12 text-center space-y-5 animate-stage-in">
                      <div className="w-16 h-16 rounded-full bg-teal-subtle border border-teal/50 text-teal flex items-center justify-center mx-auto shadow-teal">
                        <CheckCircle2 className="w-8 h-8" />
                      </div>
                      
                      <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
                        Inquiry Received &amp; Logged
                      </h3>
                      
                      <p className="text-[15.5px] text-soft-muted max-w-md mx-auto leading-relaxed">
                        Thank you, <strong className="text-white">{formData.name}</strong>. Your project details have been successfully transmitted. Ariyo will review your requirements and respond to <span className="text-teal font-mono">{formData.email}</span> within 24 business hours.
                      </p>

                      <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <Button
                          href={CONTACT.calendlyUrl}
                          target="_blank"
                          variant="primary"
                          size="md"
                          icon={Calendar}
                        >
                          Book Direct Call Instead
                        </Button>
                        <button
                          onClick={handleReset}
                          className="px-5 py-2.5 rounded-full border border-deep-blue text-xs font-mono text-soft-dim hover:text-white transition-colors cursor-pointer"
                        >
                          Submit Another Inquiry
                        </button>
                      </div>
                    </div>
                  ) : (
                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div>
                        <div className="font-mono text-xs uppercase tracking-wider text-teal font-semibold">
                          System Scope Assessment
                        </div>
                        <h3 className="text-2xl font-bold text-white tracking-tight mt-1">
                          Tell Us About Your Project
                        </h3>
                      </div>

                      {/* Server Error Alert Banner */}
                      {serverError && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-start gap-3 animate-stage-in">
                          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-400" />
                          <div className="leading-relaxed">
                            {serverError}
                          </div>
                        </div>
                      )}

                      {/* Hidden Anti-Spam Honeypot Field */}
                      <div
                        className="absolute opacity-0 -z-50 pointer-events-none h-0 w-0 overflow-hidden"
                        aria-hidden="true"
                      >
                        <label htmlFor="contact-website-field">Website</label>
                        <input
                          id="contact-website-field"
                          type="text"
                          name="website"
                          value={honeypot}
                          onChange={(e) => setHoneypot(e.target.value)}
                          tabIndex="-1"
                          autoComplete="off"
                        />
                      </div>

                      {/* Name & Email Row */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div>
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider mb-2 font-medium">
                            Full Name <span className="text-teal">*</span>
                          </label>
                          <input
                            type="text"
                            maxLength={100}
                            disabled={isSubmitting}
                            placeholder="e.g. John Miller"
                            value={formData.name}
                            onChange={(e) => {
                              setFormData({ ...formData, name: e.target.value });
                              if (errors.name) setErrors({ ...errors, name: undefined });
                              if (serverError) setServerError("");
                            }}
                            className={`w-full px-4 py-3 rounded-xl bg-midnight border ${
                              errors.name ? "border-red-500" : "border-deep-blue"
                            } text-soft-white placeholder-soft-dim text-sm focus:outline-none focus:border-teal transition-colors disabled:opacity-60`}
                          />
                          {errors.name && (
                            <p className="mt-1 text-xs text-red-400 flex items-center gap-1 font-mono">
                              <AlertCircle className="w-3.5 h-3.5" /> {errors.name}
                            </p>
                          )}
                        </div>

                        <div>
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider mb-2 font-medium">
                            Work Email <span className="text-teal">*</span>
                          </label>
                          <input
                            type="email"
                            maxLength={150}
                            disabled={isSubmitting}
                            placeholder="john@company.com"
                            value={formData.email}
                            onChange={(e) => {
                              setFormData({ ...formData, email: e.target.value });
                              if (errors.email) setErrors({ ...errors, email: undefined });
                              if (serverError) setServerError("");
                            }}
                            className={`w-full px-4 py-3 rounded-xl bg-midnight border ${
                              errors.email ? "border-red-500" : "border-deep-blue"
                            } text-soft-white placeholder-soft-dim text-sm focus:outline-none focus:border-teal transition-colors disabled:opacity-60`}
                          />
                          {errors.email && (
                            <p className="mt-1 text-xs text-red-400 flex items-center gap-1 font-mono">
                              <AlertCircle className="w-3.5 h-3.5" /> {errors.email}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Phone & Company Row */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div>
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider mb-2 font-medium">
                            Phone / WhatsApp (Optional)
                          </label>
                          <input
                            type="text"
                            maxLength={50}
                            disabled={isSubmitting}
                            placeholder="+1 (555) 000-0000"
                            value={formData.phone}
                            onChange={(e) => {
                              setFormData({ ...formData, phone: e.target.value });
                              if (errors.phone) setErrors({ ...errors, phone: undefined });
                            }}
                            className="w-full px-4 py-3 rounded-xl bg-midnight border border-deep-blue text-soft-white placeholder-soft-dim text-sm focus:outline-none focus:border-teal transition-colors disabled:opacity-60"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider mb-2 font-medium">
                            Company or Website URL
                          </label>
                          <input
                            type="text"
                            maxLength={150}
                            disabled={isSubmitting}
                            placeholder="yourcompany.com"
                            value={formData.company}
                            onChange={(e) => {
                              setFormData({ ...formData, company: e.target.value });
                              if (errors.company) setErrors({ ...errors, company: undefined });
                            }}
                            className="w-full px-4 py-3 rounded-xl bg-midnight border border-deep-blue text-soft-white placeholder-soft-dim text-sm focus:outline-none focus:border-teal transition-colors disabled:opacity-60"
                          />
                        </div>
                      </div>

                      {/* Primary Capability Need Dropdown */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div>
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider mb-2 font-medium">
                            Primary System Needed
                          </label>
                          <select
                            disabled={isSubmitting}
                            value={formData.serviceNeed}
                            onChange={(e) => setFormData({ ...formData, serviceNeed: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl bg-midnight border border-deep-blue text-soft-white text-sm focus:outline-none focus:border-teal transition-colors cursor-pointer disabled:opacity-60"
                          >
                            <option>CRM Implementation & Management</option>
                            <option>GoHighLevel Setup & Customisation</option>
                            <option>Sales & Speed-to-Lead Automation</option>
                            <option>Business Process Automation</option>
                            <option>AI Agents & Voice AI</option>
                            <option>API & Webhook Integrations</option>
                            <option>System Audit & Troubleshooting</option>
                            <option>Comprehensive End-to-End Build</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider mb-2 font-medium">
                            Project Target Timeline
                          </label>
                          <select
                            disabled={isSubmitting}
                            value={formData.timeline}
                            onChange={(e) => setFormData({ ...formData, timeline: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl bg-midnight border border-deep-blue text-soft-white text-sm focus:outline-none focus:border-teal transition-colors cursor-pointer disabled:opacity-60"
                          >
                            <option>Immediate (Within 2 weeks)</option>
                            <option>Within 2–4 weeks</option>
                            <option>1–2 months</option>
                            <option>Currently planning / scoping</option>
                          </select>
                        </div>
                      </div>

                      {/* Message / Challenge */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="block text-xs font-mono text-soft-dim uppercase tracking-wider font-medium">
                            Current Bottleneck or Project Goals <span className="text-teal">*</span>
                          </label>
                          <span className="text-[11px] font-mono text-soft-dim">
                            {formData.message.length}/3000
                          </span>
                        </div>
                        <textarea
                          rows={4}
                          maxLength={3000}
                          disabled={isSubmitting}
                          placeholder="Tell us where leads are getting stuck, what manual tasks need automating, or what software stack you're using..."
                          value={formData.message}
                          onChange={(e) => {
                            setFormData({ ...formData, message: e.target.value });
                            if (errors.message) setErrors({ ...errors, message: undefined });
                            if (serverError) setServerError("");
                          }}
                          className={`w-full px-4 py-3 rounded-xl bg-midnight border ${
                            errors.message ? "border-red-500" : "border-deep-blue"
                          } text-soft-white placeholder-soft-dim text-sm focus:outline-none focus:border-teal transition-colors leading-relaxed disabled:opacity-60`}
                        />
                        {errors.message && (
                          <p className="mt-1 text-xs text-red-400 flex items-center gap-1 font-mono">
                            <AlertCircle className="w-3.5 h-3.5" /> {errors.message}
                          </p>
                        )}
                      </div>

                      {/* Submit Button with Loading State */}
                      <div>
                        <button
                          type="submit"
                          disabled={isSubmitting}
                          className="w-full inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full font-sans font-medium text-base sm:text-lg bg-electric text-white hover:bg-electric-light transition-all duration-200 cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed shadow-sm hover:shadow-highlight active:scale-[0.98]"
                        >
                          {isSubmitting ? (
                            <>
                              <Loader2 className="w-5 h-5 animate-spin" />
                              <span>Submitting Inquiry...</span>
                            </>
                          ) : (
                            <>
                              <Send className="w-5 h-5" />
                              <span>Submit Project Inquiry</span>
                            </>
                          )}
                        </button>
                      </div>

                      <div className="flex items-center justify-between text-xs font-mono text-soft-dim pt-2">
                        <span className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal" /> Zero Spam Guarantee
                        </span>
                        <span>Direct response within 24 hours</span>
                      </div>
                    </form>
                  )}

                </div>
              </ScrollReveal>
            </div>

          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
