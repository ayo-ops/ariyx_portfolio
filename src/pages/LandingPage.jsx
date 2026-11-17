import React, { useState, useEffect } from "react";
import { Link } from "../router";
import Logo from "../components/common/Logo";
import { CONTACT } from "../data/navigation";
import { PROJECTS } from "../data/projects";
import { TESTIMONIALS, VIDEO_TESTIMONIAL } from "../data/testimonials";
import VideoModal from "../components/home/VideoModal";
import ProjectModal from "../components/home/ProjectModal";
import {
  Compass,
  ArrowUpRight,
  ArrowRight,
  MessageSquare,
  Globe,
  Star,
  Play,
  ChevronLeft,
  ChevronRight,
  Check,
} from "lucide-react";

// Kinetic moving letters component for headline
function AnimatedLetters({ text, className = "", delayOffset = 0, gradient = false }) {
  const words = text.split(" ");
  return (
    <span className={`inline-block ${className}`}>
      {words.map((word, wIdx) => {
        let offset = 0;
        for (let i = 0; i < wIdx; i++) {
          offset += words[i].length;
        }

        return (
          <span key={wIdx} className="inline-block whitespace-nowrap mr-[0.24em] last:mr-0">
            {word.split("").map((char, cIdx) => {
              const letterIdx = offset + cIdx;
              const delay = (delayOffset + letterIdx * 0.08).toFixed(2);
              return (
                <span
                  key={cIdx}
                  className={`animate-letter-wave transition-all duration-200 hover:-translate-y-3 hover:scale-110 cursor-default select-none ${
                    gradient
                      ? "text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-teal-300 to-blue-500"
                      : "text-white hover:text-teal-300"
                  }`}
                  style={{
                    animationDelay: `${delay}s`,
                  }}
                >
                  {char}
                </span>
              );
            })}
          </span>
        );
      })}
    </span>
  );
}

export default function LandingPage() {
  const [isVideoOpen, setIsVideoOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [activeReviewIdx, setActiveReviewIdx] = useState(0);
  const [openFaqIdx, setOpenFaqIdx] = useState(0);

  useEffect(() => {
    document.title = "Ariyx Systems";
  }, []);

  // State for Section 5: Interactive System Diagnostic
  const [guideBusiness, setGuideBusiness] = useState("");
  const [guideGoal, setGuideGoal] = useState("");
  const [guideResult, setGuideResult] = useState(null);
  const [isGeneratingGuide, setIsGeneratingGuide] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);

  const handleGuideSubmit = (e) => {
    e.preventDefault();
    if (!guideBusiness || !guideGoal) return;
    setIsGeneratingGuide(true);
    setTimeout(() => {
      setIsGeneratingGuide(false);
      setGuideResult({
        title: "Speed-to-Lead & Automated CRM Pipeline",
        summary: `For your business (${guideBusiness.trim()}) targeting "${guideGoal.trim()}", the highest-ROI system is an automated 60-second inbound response engine paired with a structured GoHighLevel follow-up sequence.`,
        deliverables: [
          "Instant sub-60s SMS & WhatsApp response on new enquiries",
          "Automated 7-touch follow-up cadence that halts on reply",
          "Direct self-scheduling calendar booking integration",
          "Centralized CRM dashboard eliminating manual spreadsheets",
        ],
        timeline: "2 – 3 Weeks to Complete Deployment",
      });
    }, 600);
  };

  const nextReview = () => {
    setActiveReviewIdx((prev) => (prev + 1) % TESTIMONIALS.length);
  };
  const prevReview = () => {
    setActiveReviewIdx((prev) => (prev - 1 + TESTIMONIALS.length) % TESTIMONIALS.length);
  };

  const activeReview = TESTIMONIALS[activeReviewIdx];

  const FAQS = [
    {
      q: "Is the 30-minute strategy session really free?",
      a: "Yes, 100% free. We get on screen share, inspect your current lead workflow, spot the bottlenecks where revenue is leaking, and give you an actionable automation roadmap you can keep.",
    },
    {
      q: "What if my business doesn't have a modern CRM yet?",
      a: "That's completely fine. We design and build everything from the ground up—configuring GoHighLevel as your single command center, connecting your forms, and programming your automated follow-ups.",
    },
    {
      q: "What if we already use GoHighLevel, HubSpot, or other tools?",
      a: "We work directly with your existing infrastructure. We audit where leads are dropping out, rebuild messy workflows, eliminate broken triggers, and integrate your platforms cleanly via webhooks.",
    },
    {
      q: "What tools and platforms do you engineer with?",
      a: "GoHighLevel, HubSpot, ActiveCampaign, Make.com, Zapier, Twilio, WhatsApp Business API, Stripe, Calendly, and custom REST API endpoints.",
    },
    {
      q: "Will you actually build, test, and deploy it for us?",
      a: "Yes. We are systems engineers, not coaches. We handle 100% of the build, technical setup, webhook testing, team video walkthroughs, and 30 days of post-launch optimization.",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-blue-600 selection:text-white relative">
      
      {/* ==================== STICKY FLOATING WHATSAPP BUTTON (LOWER RIGHT) ==================== */}
      <a
        href={CONTACT.whatsappUrl}
        target="_blank"
        rel="noreferrer"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-full bg-[#25D366] px-5 py-3.5 text-white font-extrabold text-base shadow-2xl hover:bg-[#20bd5a] hover:scale-105 transition-all duration-300 group border-2 border-white/20"
        aria-label="WhatsApp"
      >
        <span className="relative flex h-3.5 w-3.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-white"></span>
        </span>
        <MessageSquare className="w-5 h-5 fill-current" />
        <span className="font-bold">WhatsApp</span>
      </a>

      {/* ==================== HEADER ==================== */}
      <header className="absolute inset-x-0 top-0 z-30">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
          {/* Logo — exact official asset from website with wordmark */}
          <Link to="/growth" className="focus:outline-none">
            <Logo size="lg" />
          </Link>

          {/* Nav Controls */}
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="hidden sm:inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-5 py-2.5 text-sm font-bold uppercase tracking-wider text-white hover:bg-white/10 transition"
            >
              <Globe className="w-4 h-4 text-teal-400" />
              <span>Explore Full Website</span>
            </Link>

            <a
              href={CONTACT.whatsappUrl}
              target="_blank"
              rel="noreferrer"
              className="hidden md:inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-5 py-2.5 text-sm font-bold uppercase tracking-wider text-white hover:bg-white/10 transition"
            >
              <MessageSquare className="w-4 h-4 text-emerald-400" />
              <span>WhatsApp</span>
            </a>

            <a
              href={CONTACT.calendlyUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded-xl bg-blue-600 px-6 py-3 text-base font-extrabold text-white shadow-lg shadow-blue-600/30 transition hover:-translate-y-0.5 hover:brightness-110"
            >
              Book a Call
            </a>
          </div>
        </div>
      </header>

      {/* ==================== SECTION 0: HERO (MIDNIGHT NAVY #101B2D) ==================== */}
      <section className="bg-[#101B2D] px-6 pb-24 pt-40 text-center text-white relative overflow-hidden">
        {/* Eyebrow Badge */}
        <span className="inline-block rounded-full border border-blue-400/40 bg-blue-500/10 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-white uppercase">
          CUSTOM CRM &amp; AUTOMATION ARCHITECTURE
        </span>

        {/* Clean 2-Line Headline — Bold, Massive & Animated Moving Letters */}
        <h1 className="mx-auto mt-8 max-w-6xl text-5xl sm:text-7xl lg:text-8xl xl:text-[88px] font-black uppercase leading-[1.04] tracking-tight">
          <AnimatedLetters text="TURN YOUR LEADS INTO" className="block text-white" delayOffset={0} />
          <AnimatedLetters text="BOOKED CLIENTS & REVENUE." className="block mt-2 sm:mt-3" delayOffset={1.4} gradient={true} />
        </h1>

        {/* Subhead */}
        <p className="mx-auto mt-8 max-w-4xl text-xl sm:text-2xl lg:text-3xl text-slate-200 leading-relaxed font-normal opacity-95">
          Stop losing qualified leads to slow response times, messy inboxes, and forgotten follow-ups.
          We engineer custom GoHighLevel CRM workflows, instant 60-second response systems, and automated follow-up that run hands-free.
        </p>

        {/* Primary Action Button */}
        <div className="mt-12 flex flex-col items-center gap-4">
          <a
            href={CONTACT.calendlyUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-2xl bg-blue-600 px-10 py-5 text-xl font-extrabold text-white shadow-xl shadow-blue-600/40 transition hover:-translate-y-0.5 hover:brightness-110 cursor-pointer"
          >
            Claim Your Free Strategy Session →
          </a>
          <p className="text-base sm:text-lg text-slate-300 font-medium">
            30-Minute Live Pipeline Audit · Zero Sales Pitch · Custom Workflow Map
          </p>
        </div>

        {/* 4 Sample Browser Cards — Using Deep Navy #16253D (No Black) */}
        <div className="mx-auto mt-16 grid max-w-6xl gap-6 sm:grid-cols-2 text-left">
          
          {/* Card 1 */}
          <div
            onClick={() => setSelectedProject(PROJECTS[0])}
            className="group block overflow-hidden rounded-2xl border border-white/10 bg-[#16253D] cursor-pointer transition hover:border-blue-400/60 shadow-xl"
          >
            <div className="flex items-center gap-2 px-5 py-3.5 bg-[#121E33] border-b border-white/10 text-slate-300">
              <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
              <p className="ml-auto text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">Speed-to-Lead Engine</p>
              <ArrowUpRight className="ml-2 h-4 w-4 text-slate-300 group-hover:text-white" />
            </div>
            <div className="relative isolate flex min-h-80 flex-col justify-end overflow-hidden p-8">
              <img
                src="/projects/mockup-1.png"
                alt="Lead Capture & Conversion Engine"
                className="absolute inset-0 -z-20 h-full w-full object-cover transition duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 -z-10 bg-gradient-to-t from-[#101B2D] via-[#101B2D]/70 to-transparent" />
              <p className="mb-auto text-xs font-black tracking-widest text-teal-400 uppercase">ARIYX SYSTEMS</p>
              <p className="mt-8 text-xs font-bold tracking-widest text-slate-200 uppercase">INSTANT MULTI-CHANNEL RESPONSE</p>
              <h3 className="mt-2 max-w-md text-3xl sm:text-4xl font-black leading-tight text-white">Capture, qualify &amp; close.</h3>
              <span className="mt-5 w-fit rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-bold text-white">View system ↗</span>
            </div>
            <div className="flex items-center justify-between px-6 py-4 text-base font-bold text-slate-200 border-t border-white/10 bg-[#121E33]">
              <span>Automated Lead Intake &amp; Booking</span>
              <span className="flex items-center gap-2 text-blue-400 font-bold">Open sample <ArrowUpRight className="h-4 w-4" /></span>
            </div>
          </div>

          {/* Card 2 */}
          <div
            onClick={() => setSelectedProject(PROJECTS[1])}
            className="group block overflow-hidden rounded-2xl border border-white/10 bg-[#16253D] cursor-pointer transition hover:border-blue-400/60 shadow-xl"
          >
            <div className="flex items-center gap-2 px-5 py-3.5 bg-[#121E33] border-b border-white/10 text-slate-300">
              <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
              <p className="ml-auto text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">Clinic CRM System</p>
              <ArrowUpRight className="ml-2 h-4 w-4 text-slate-300 group-hover:text-white" />
            </div>
            <div className="relative isolate flex min-h-80 flex-col justify-end overflow-hidden p-8">
              <img
                src="/projects/mockup-2.png"
                alt="Clinic Intake System"
                className="absolute inset-0 -z-20 h-full w-full object-cover transition duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 -z-10 bg-gradient-to-t from-[#101B2D] via-[#101B2D]/70 to-transparent" />
              <p className="mb-auto text-xs font-black tracking-widest text-teal-400 uppercase">MEDSPA &amp; CLINIC PIPELINE</p>
              <p className="mt-8 text-xs font-bold tracking-widest text-slate-200 uppercase">24/7 APPOINTMENT BOOKING</p>
              <h3 className="mt-2 max-w-md text-3xl sm:text-4xl font-black leading-tight text-white">Zero no-shows. Full room schedules.</h3>
              <span className="mt-5 w-fit rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-bold text-white">View system ↗</span>
            </div>
            <div className="flex items-center justify-between px-6 py-4 text-base font-bold text-slate-200 border-t border-white/10 bg-[#121E33]">
              <span>Patient Triage &amp; SMS Reminders</span>
              <span className="flex items-center gap-2 text-blue-400 font-bold">Open sample <ArrowUpRight className="h-4 w-4" /></span>
            </div>
          </div>

          {/* Card 3 */}
          <div
            onClick={() => setSelectedProject(PROJECTS[2])}
            className="group block overflow-hidden rounded-2xl border border-white/10 bg-[#16253D] cursor-pointer transition hover:border-blue-400/60 shadow-xl"
          >
            <div className="flex items-center gap-2 px-5 py-3.5 bg-[#121E33] border-b border-white/10 text-slate-300">
              <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
              <p className="ml-auto text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">Service Contractor</p>
              <ArrowUpRight className="ml-2 h-4 w-4 text-slate-300 group-hover:text-white" />
            </div>
            <div className="relative isolate flex min-h-80 flex-col justify-end overflow-hidden p-8">
              <img
                src="/projects/mockup-3.png"
                alt="Contractor Estimate System"
                className="absolute inset-0 -z-20 h-full w-full object-cover transition duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 -z-10 bg-gradient-to-t from-[#101B2D] via-[#101B2D]/70 to-transparent" />
              <p className="mb-auto text-xs font-black tracking-widest text-teal-400 uppercase">FIELD ESTIMATE DISPATCH</p>
              <p className="mt-8 text-xs font-bold tracking-widest text-slate-200 uppercase">HOME SERVICES PIPELINE</p>
              <h3 className="mt-2 max-w-md text-3xl sm:text-4xl font-black leading-tight text-white">Instant estimates while on-site.</h3>
              <span className="mt-5 w-fit rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-bold text-white">View system ↗</span>
            </div>
            <div className="flex items-center justify-between px-6 py-4 text-base font-bold text-slate-200 border-t border-white/10 bg-[#121E33]">
              <span>Contractor Quote &amp; Deposit Pipeline</span>
              <span className="flex items-center gap-2 text-blue-400 font-bold">Open sample <ArrowUpRight className="h-4 w-4" /></span>
            </div>
          </div>

          {/* Card 4 */}
          <div
            onClick={() => setSelectedProject(PROJECTS[3])}
            className="group block overflow-hidden rounded-2xl border border-white/10 bg-[#16253D] cursor-pointer transition hover:border-blue-400/60 shadow-xl"
          >
            <div className="flex items-center gap-2 px-5 py-3.5 bg-[#121E33] border-b border-white/10 text-slate-300">
              <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
              <p className="ml-auto text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">Consulting CRM</p>
              <ArrowUpRight className="ml-2 h-4 w-4 text-slate-300 group-hover:text-white" />
            </div>
            <div className="relative isolate flex min-h-80 flex-col justify-end overflow-hidden p-8">
              <img
                src="/projects/mockup-4.png"
                alt="Consulting Application Funnel"
                className="absolute inset-0 -z-20 h-full w-full object-cover transition duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 -z-10 bg-gradient-to-t from-[#101B2D] via-[#101B2D]/70 to-transparent" />
              <p className="mb-auto text-xs font-black tracking-widest text-teal-400 uppercase">HIGH-TICKET ADVISORY</p>
              <p className="mt-8 text-xs font-bold tracking-widest text-slate-200 uppercase">PRE-QUALIFIED APPLICATION FLOW</p>
              <h3 className="mt-2 max-w-md text-3xl sm:text-4xl font-black leading-tight text-white">Pre-educated buyers on your Zoom.</h3>
              <span className="mt-5 w-fit rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-bold text-white">View system ↗</span>
            </div>
            <div className="flex items-center justify-between px-6 py-4 text-base font-bold text-slate-200 border-t border-white/10 bg-[#121E33]">
              <span>Application Qualification Pipeline</span>
              <span className="flex items-center gap-2 text-blue-400 font-bold">Open sample <ArrowUpRight className="h-4 w-4" /></span>
            </div>
          </div>

        </div>

        {/* Bottom Bar */}
        <p className="mx-auto mt-16 max-w-6xl border-t border-white/10 pt-8 text-sm font-bold tracking-[0.22em] text-slate-400 uppercase">
          TRUSTED BY HIGH-GROWTH BUSINESSES &amp; SERVICE LEADERS
        </p>
      </section>

      {/* ==================== SECTION 1: THE OPERATIONAL FOUNDATION (CRISP WHITE) ==================== */}
      <section className="bg-white px-6 py-28 text-center text-slate-900">
        <span className="inline-block rounded-full border border-blue-600/30 bg-blue-50 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-blue-600 uppercase">
          THE OPERATIONAL FOUNDATION
        </span>

        <h2 className="mx-auto mt-8 max-w-5xl text-4xl font-black uppercase leading-tight md:text-6xl lg:text-7xl text-slate-950">
          Your business doesn't need more software. <br />
          <span className="text-blue-600">It needs a connected system.</span>
        </h2>

        <p className="mt-6 text-2xl sm:text-3xl font-bold text-slate-900">
          Buying another tool won't fix a broken lead process.
        </p>

        <div className="mt-8 space-y-2 text-xl sm:text-2xl text-slate-700 font-medium">
          <p>Your service is different.</p>
          <p>Your target buyers are different.</p>
          <p>Your pricing and sales cycle are different.</p>
          <p>Your team's daily workflow is different.</p>
        </div>

        <p className="mt-8 text-xl sm:text-2xl text-slate-800">
          So why try to run your revenue on a generic out-of-the-box template?
        </p>
        <p className="mt-3 text-2xl font-black text-slate-950">
          We start by mapping how your business actually makes money.
        </p>

        {/* Pipeline Pills */}
        <div className="mx-auto mt-12 flex max-w-5xl flex-wrap items-center justify-center gap-3.5 font-black text-base sm:text-lg">
          <span className="flex items-center gap-3">
            <span className="rounded-xl border border-slate-300 bg-slate-100 px-5 py-3 text-slate-900">INBOUND LEAD</span>
            <span className="text-blue-600 font-black">→</span>
          </span>
          <span className="flex items-center gap-3">
            <span className="rounded-xl border border-slate-300 bg-slate-100 px-5 py-3 text-slate-900">60-SEC RESPONSE</span>
            <span className="text-blue-600 font-black">→</span>
          </span>
          <span className="flex items-center gap-3">
            <span className="rounded-xl border border-slate-300 bg-slate-100 px-5 py-3 text-slate-900">QUALIFICATION</span>
            <span className="text-blue-600 font-black">→</span>
          </span>
          <span className="flex items-center gap-3">
            <span className="rounded-xl border border-slate-300 bg-slate-100 px-5 py-3 text-slate-900">MULTI-TOUCH NURTURE</span>
            <span className="text-blue-600 font-black">→</span>
          </span>
          <span className="flex items-center gap-3">
            <span className="rounded-xl border border-slate-300 bg-slate-100 px-5 py-3 text-slate-900">CALENDAR BOOKING</span>
            <span className="text-blue-600 font-black">→</span>
          </span>
          <span className="flex items-center gap-3">
            <span className="rounded-xl border border-slate-300 bg-slate-100 px-5 py-3 text-slate-900">CLOSED REVENUE</span>
          </span>
        </div>

        <p className="mt-10 text-xl sm:text-2xl text-slate-700">We design the system around your real sales workflow.</p>

        <h3 className="mt-12 text-3xl sm:text-4xl font-black uppercase text-slate-950">
          BUSINESS LOGIC FIRST. <span className="text-blue-600">AUTOMATION SECOND.</span>
        </h3>
        <p className="mt-4 text-lg text-slate-600 font-medium">
          Because the best software in the world won't make you money if the pipeline leaks.
        </p>
      </section>

      {/* ==================== SECTION 2: END TO END IMPLEMENTATION (MIDNIGHT NAVY) ==================== */}
      <section className="bg-[#101B2D] px-6 py-28 text-center text-white">
        <span className="inline-block rounded-full border border-blue-400/60 bg-blue-500/10 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-white uppercase">
          FULL-STACK AUTOMATION DELIVERY
        </span>

        <h2 className="mt-8 text-4xl font-black uppercase md:text-6xl lg:text-7xl text-white">
          We engineer the entire pipeline for you. <br />
          <span className="bg-gradient-to-r from-blue-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
            From first click to closed deal.
          </span>
        </h2>

        {/* 6 Cards Grid — Using Deep Navy #16253D */}
        <div className="mx-auto mt-16 grid max-w-6xl gap-6 text-left md:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8 hover:border-blue-400/40 transition">
            <h3 className="text-xl font-black uppercase text-blue-400">Custom CRM Architecture</h3>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              Clean GoHighLevel setups with customized pipelines, logical deal stages, and zero clutter so your team always knows who to follow up with.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8 hover:border-blue-400/40 transition">
            <h3 className="text-xl font-black uppercase text-blue-400">60-Second Speed-To-Lead</h3>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              Instant automated SMS, email, and WhatsApp responses within 60 seconds of any enquiry landing—engaging buyers while they're hot.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8 hover:border-blue-400/40 transition">
            <h3 className="text-xl font-black uppercase text-blue-400">Automated Follow-Up Cadence</h3>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              Condition-based email, SMS, and WhatsApp sequences that nurture undecided leads and automatically pause the second a prospect replies.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8 hover:border-blue-400/40 transition">
            <h3 className="text-xl font-black uppercase text-blue-400">No-Show Elimination Drips</h3>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              Two-way attendance confirmations, pre-call case studies, and 1-click reschedule buttons that cut appointment no-shows by 50%+.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8 hover:border-blue-400/40 transition">
            <h3 className="text-xl font-black uppercase text-blue-400">24/7 Conversational AI Voice</h3>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              AI phone receptionists that answer after-hours calls in a natural human voice, screen qualification details, and book straight to your live calendar.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8 hover:border-blue-400/40 transition">
            <h3 className="text-xl font-black uppercase text-blue-400">Workflow &amp; Webhook Middleware</h3>
            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              Connecting your website, Stripe invoicing, Make.com, Zapier, and Slack alerts so information moves instantly without copy-pasting.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-14 flex flex-col items-center gap-4">
          <a
            href={CONTACT.calendlyUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-2xl bg-blue-600 px-10 py-5 text-xl font-extrabold text-white shadow-xl shadow-blue-600/40 transition hover:-translate-y-0.5 hover:brightness-110"
          >
            BOOK MY FREE SYSTEMS STRATEGY SESSION →
          </a>
          <p className="text-base text-slate-300">⚡ 100% Free • Custom Action Plan • Direct Engineer Conversation</p>
        </div>
      </section>

      {/* ==================== SECTION 3: PROVEN WORKFLOW ARCHITECTURES (WHITE) ==================== */}
      <section className="bg-white px-6 py-28 text-center text-slate-900">
        <span className="inline-block rounded-full border border-blue-600/30 bg-blue-50 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-blue-600 uppercase">
          PROVEN WORKFLOW ARCHITECTURES
        </span>

        <h2 className="mt-8 text-4xl font-black uppercase md:text-6xl text-slate-950">
          Whatever service you deliver...
        </h2>
        <p className="mt-4 text-2xl sm:text-3xl font-extrabold text-blue-600">
          There's An Automated System For It.
        </p>

        {/* 8 Cards Grid */}
        <div className="mx-auto mt-16 grid max-w-6xl gap-6 text-left sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">Speed-to-Lead Engines</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Engage website and paid ad enquiries via SMS and email in under 60 seconds.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">High-Ticket Application Funnels</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Filter out unqualified prospects and deliver pre-sold buyers to your calendar.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">Clinic Intake &amp; Triage</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">24/7 AI call answering, WhatsApp reminders, and automated digital intake paperwork.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">Contractor Estimate Pipelines</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Instant quote scheduling, automated proposal follow-up, and deposit collection.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">Agency Client Onboarding</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Deal won in CRM triggers automated contracts, Stripe billing, and Slack channels.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">Cold Database Reactivation</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Revive old, dormant contacts with automated 2-way conversational text campaigns.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">24/7 AI Phone Assistants</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Never miss an evening or weekend caller. AI qualifies and books directly to your calendar.</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
            <h3 className="font-black uppercase text-slate-950 text-lg">Attendance Warm-Up Sequences</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">Multi-touch SMS reminders that cut consultation no-shows and prepare clients for the call.</p>
          </div>
        </div>
      </section>

      {/* ==================== SECTION 4: SAMPLE SYSTEMS & REAL PROOF (SOFT GREY) ==================== */}
      <section className="bg-[#F8FAFC] px-6 py-28 text-center text-slate-900 border-t border-slate-200">
        <span className="inline-block rounded-full border border-blue-600/30 bg-blue-50 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-blue-600 uppercase">
          VERIFIED PRODUCTION RESULTS
        </span>

        <h2 className="mt-8 text-4xl font-black uppercase md:text-6xl lg:text-7xl text-slate-950">
          Systems built for <span className="text-blue-600">growth-minded operators.</span>
        </h2>
        <p className="mx-auto mt-4 max-w-3xl text-xl text-slate-600 leading-relaxed">
          Clinics, service contractors, agencies, coaches, and B2B consultancies. Real environments engineered for conversion and speed.
        </p>

        {/* Patty Jackson Video Feature */}
        <div className="mx-auto mt-14 max-w-4xl rounded-3xl border border-slate-200 bg-white p-8 sm:p-10 shadow-sm text-left">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-5">
              <div
                onClick={() => setIsVideoOpen(true)}
                className="group relative aspect-video rounded-2xl overflow-hidden bg-[#101B2D] cursor-pointer shadow-md"
              >
                <img
                  src={VIDEO_TESTIMONIAL.poster}
                  alt="Patty Jackson Video Review"
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                />
                <div className="absolute inset-0 bg-[#101B2D]/40 group-hover:bg-[#101B2D]/20 transition-colors" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-xl group-hover:scale-110 transition">
                    <Play className="w-7 h-7 ml-1 fill-current" />
                  </div>
                </div>
              </div>
            </div>

            <div className="md:col-span-7 space-y-3">
              <span className="text-xs font-black font-mono text-blue-600 uppercase tracking-wider">
                Verified Client Interview
              </span>
              <h3 className="text-2xl sm:text-3xl font-black text-slate-950 leading-tight">
                How Patty Jackson Automated Her Lead Capture &amp; Email Follow-Up
              </h3>
              <p className="text-base text-slate-600 leading-relaxed">
                {VIDEO_TESTIMONIAL.caption}
              </p>
              <button
                onClick={() => setIsVideoOpen(true)}
                className="inline-flex items-center gap-2 pt-2 text-base font-extrabold text-blue-600 hover:text-blue-700 cursor-pointer"
              >
                Watch Patty's 1-Minute Video Review →
              </button>
            </div>
          </div>
        </div>

        {/* Real Written Testimonials Carousel */}
        <div className="mx-auto mt-14 max-w-4xl rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 shadow-sm text-left">
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm font-extrabold uppercase tracking-wider text-blue-600 bg-blue-50 px-4 py-1.5 rounded-full border border-blue-200">
              {activeReview.highlight}
            </span>
            <div className="flex items-center gap-1.5 text-amber-500">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-current" />
              ))}
            </div>
          </div>

          <blockquote className="text-xl sm:text-2xl font-medium text-slate-900 leading-relaxed mb-8">
            &ldquo;{activeReview.review}&rdquo;
          </blockquote>

          <div className="flex items-center justify-between pt-6 border-t border-slate-100">
            <div>
              <p className="text-lg font-black text-slate-950">{activeReview.name}</p>
              <p className="text-sm text-slate-500">{activeReview.business}</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={prevReview}
                className="w-10 h-10 rounded-full border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-700 cursor-pointer"
                aria-label="Previous review"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm font-mono text-slate-500 min-w-[50px] text-center font-bold">
                {activeReviewIdx + 1} / {TESTIMONIALS.length}
              </span>
              <button
                onClick={nextReview}
                className="w-10 h-10 rounded-full border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-700 cursor-pointer"
                aria-label="Next review"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12 flex flex-col items-center gap-3">
          <a
            href={CONTACT.calendlyUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-2xl bg-blue-600 px-10 py-5 text-xl font-extrabold text-white shadow-xl shadow-blue-600/30 transition hover:-translate-y-0.5 hover:brightness-110"
          >
            BOOK A CALL FOR YOUR NICHE →
          </a>
          <p className="text-base text-slate-500">See what your custom system could look like</p>
        </div>
      </section>

      {/* ==================== SECTION 5: INTERACTIVE SYSTEM DIAGNOSTIC (WHITE) ==================== */}
      <section id="funnel-guide" className="border-y border-slate-200 bg-white px-6 py-28 text-slate-900">
        <div className="mx-auto grid max-w-6xl gap-14 lg:grid-cols-[.85fr_1.15fr] items-start">
          
          {/* Left Column */}
          <div>
            <Compass className="h-12 w-12 text-blue-600" />
            <p className="mt-6 text-sm font-black text-blue-600 tracking-wider uppercase">INTERACTIVE SYSTEM DIAGNOSTIC</p>
            <h2 className="mt-5 text-4xl font-black uppercase leading-tight md:text-5xl lg:text-6xl text-slate-950">
              Find your<br />starting blueprint.
            </h2>
            <p className="mt-6 text-xl text-slate-600 leading-relaxed">
              Your business model. Your current bottlenecks. The exact automation architecture to fix it.
            </p>
          </div>

          {/* Right Column: Form */}
          <div>
            <form onSubmit={handleGuideSubmit} className="space-y-6">
              <div>
                <label htmlFor="guide-business" className="text-lg font-bold text-slate-900 block">
                  What kind of business do you run?
                </label>
                <textarea
                  id="guide-business"
                  minLength={4}
                  maxLength={2000}
                  required
                  value={guideBusiness}
                  onChange={(e) => setGuideBusiness(e.target.value)}
                  placeholder="e.g. Roofing contractor, MedSpa clinic, Growth agency, Executive coach..."
                  rows={3}
                  className="mt-3 block w-full resize-y rounded-xl border border-slate-300 bg-white p-4 text-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                ></textarea>
              </div>

              <div>
                <label htmlFor="guide-goals" className="text-lg font-bold text-slate-900 block">
                  Where are leads currently getting lost in your business?
                </label>
                <textarea
                  id="guide-goals"
                  minLength={4}
                  maxLength={2000}
                  required
                  value={guideGoal}
                  onChange={(e) => setGuideGoal(e.target.value)}
                  placeholder="e.g. Taking hours to reply, high consultation no-shows, forgetting to follow up, messy spreadsheets..."
                  rows={3}
                  className="mt-3 block w-full resize-y rounded-xl border border-slate-300 bg-white p-4 text-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                ></textarea>
              </div>

              <button
                type="submit"
                disabled={isGeneratingGuide}
                className="inline-flex items-center justify-center gap-3 rounded-xl shadow-lg h-auto w-full whitespace-normal bg-blue-600 px-8 py-5 text-lg font-extrabold text-white hover:bg-blue-700 transition cursor-pointer"
              >
                <span>{isGeneratingGuide ? "Analyzing your pipeline..." : "Generate my recommended system"}</span>
                <ArrowUpRight className="w-5 h-5" />
              </button>

              <p className="text-sm text-slate-500">
                Actionable system recommendations based on your business model. No generic fluff.
              </p>
            </form>

            {/* Generated System Result Box */}
            {guideResult && (
              <div className="mt-8 rounded-2xl border border-blue-200 bg-blue-50/80 p-8 animate-fade-in shadow-sm">
                <span className="text-xs font-black uppercase tracking-wider text-blue-700 font-mono">
                  Recommended Architecture
                </span>
                <h3 className="text-2xl sm:text-3xl font-black text-slate-950 mt-2 mb-4">
                  {guideResult.title}
                </h3>
                <p className="text-slate-700 text-base sm:text-lg leading-relaxed mb-6">
                  {guideResult.summary}
                </p>

                <div className="space-y-3 mb-6">
                  {guideResult.deliverables.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3 text-base text-slate-900 font-semibold">
                      <Check className="w-5 h-5 text-blue-600 shrink-0" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-blue-200">
                  <span className="text-sm text-slate-700 font-medium">
                    Build Timeline: <strong className="text-slate-950 font-bold">{guideResult.timeline}</strong>
                  </span>
                  <a
                    href={CONTACT.calendlyUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 text-base font-extrabold text-white hover:bg-blue-700 transition"
                  >
                    <span>Review Blueprint On A Call</span>
                    <ArrowRight className="w-4 h-4" />
                  </a>
                </div>
              </div>
            )}
          </div>

        </div>
      </section>

      {/* ==================== SECTION 6: WHO WE BUILD FOR (SOFT GREY) ==================== */}
      <section className="bg-[#F8FAFC] px-6 py-28 text-center text-slate-900 border-b border-slate-200">
        <span className="inline-block rounded-full border border-blue-600/30 bg-blue-50 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-blue-600 uppercase">
          WHO WE BUILD FOR
        </span>

        <h2 className="mt-8 text-4xl font-black uppercase md:text-6xl text-slate-950">
          Systems engineered for <span className="text-blue-600">high-value service businesses.</span>
        </h2>

        {/* Large Pill Badges */}
        <div className="mx-auto mt-14 flex max-w-5xl flex-wrap justify-center gap-4">
          <span className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-base sm:text-lg font-black text-slate-900 shadow-sm">
            Service Contractors (HVAC, Roofing, Solar, Plumbing)
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-base sm:text-lg font-black text-slate-900 shadow-sm">
            Medical, Dental &amp; Aesthetics Clinics
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-base sm:text-lg font-black text-slate-900 shadow-sm">
            Marketing &amp; Growth Agencies
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-base sm:text-lg font-black text-slate-900 shadow-sm">
            High-Ticket Coaches &amp; Mentors
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-base sm:text-lg font-black text-slate-900 shadow-sm">
            B2B Professional Services &amp; Consultancies
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-base sm:text-lg font-black text-slate-900 shadow-sm">
            Real Estate &amp; Property Developers
          </span>
        </div>
      </section>

      {/* ==================== SECTION 7: FOUNDER SPOTLIGHT (MIDNIGHT NAVY) ==================== */}
      <section className="bg-[#101B2D] px-6 py-28 text-white">
        <div className="mx-auto grid max-w-6xl items-center gap-14 md:grid-cols-2">
          {/* Founder Image */}
          <img
            src="/founder.jpg"
            alt="Ariyo Emmanuel, Founder of Ariyx Systems"
            width={784}
            height={864}
            loading="lazy"
            className="w-full rounded-3xl shadow-2xl object-cover aspect-[4/5]"
          />

          {/* Bio */}
          <div>
            <span className="inline-block rounded-full border border-blue-400/60 bg-blue-500/10 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-white uppercase">
              DIRECT ENGINEERING ACCESS
            </span>

            <h2 className="mt-6 text-4xl font-black uppercase md:text-5xl lg:text-6xl text-white">
              Hi, I'm <span className="bg-gradient-to-r from-blue-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">Emmanuel.</span>
            </h2>

            <div className="mt-8 space-y-4 text-lg sm:text-xl text-slate-200 leading-relaxed font-normal opacity-95">
              <p>I'm the founder and lead systems architect at Ariyx Systems.</p>
              <p>
                I help businesses turn their enquiries, ad spend, and manual processes into automated revenue engines—through custom GoHighLevel setups, sub-minute lead response, multi-channel nurture, and AI voice agents.
              </p>
              <p>Here is the reality most business owners discover too late:</p>
              <p className="text-xl sm:text-2xl font-black text-white italic border-l-4 border-teal-400 pl-4 py-1">
                "Most businesses don't have a lead problem. They have a plumbing problem."
              </p>
              <p>
                Enquiries pour in from your website and ads, but disappear through delayed replies, disorganised inboxes, and forgotten follow-ups.
              </p>
              <p>
                When you hire a bloated agency, you get sold by an account director and handed off to a junior intern who barely understands your sales workflow.
              </p>
              <p>
                When you partner with Ariyx, you work directly with me. Every pipeline, webhook, database field, and automated sequence is engineered, tested, and launched personally.
              </p>
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-5">
              <a
                href={CONTACT.calendlyUrl}
                target="_blank"
                rel="noreferrer"
                className="rounded-2xl bg-blue-600 px-8 py-4 text-lg font-extrabold text-white hover:brightness-110 transition"
              >
                Book a Strategy Call →
              </a>
              <Link
                to="/about"
                className="text-base text-slate-300 hover:text-white underline underline-offset-4 transition"
              >
                Read our full credentials &amp; background
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ==================== SECTION 8: 30-MIN STRATEGY SESSION (WHITE) ==================== */}
      <section className="bg-white px-6 py-28 text-center text-slate-900">
        <span className="inline-block rounded-full border border-blue-600/30 bg-blue-50 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-blue-600 uppercase">
          COMPLIMENTARY 30-MINUTE PIPELINE DIAGNOSTIC
        </span>

        <h2 className="mt-8 text-4xl font-black uppercase md:text-6xl lg:text-7xl text-slate-950">
          Let's find where leads are <br className="hidden sm:inline" />
          <span className="text-blue-600">leaking out of your pipeline.</span>
        </h2>

        {/* 4 Cards Grid */}
        <div className="mx-auto mt-16 grid max-w-6xl gap-6 text-left md:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
            <span className="text-5xl font-black text-blue-600 font-mono">01</span>
            <h3 className="mt-4 font-black uppercase text-slate-950 text-xl">Where You Are Today</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">
              Your traffic sources, enquiry channels, current CRM tools, and daily sales workload.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
            <span className="text-5xl font-black text-blue-600 font-mono">02</span>
            <h3 className="mt-4 font-black uppercase text-slate-950 text-xl">Where Deals Drop Off</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">
              We'll inspect your speed-to-lead, follow-up cadence, and where prospects are going cold.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
            <span className="text-5xl font-black text-blue-600 font-mono">03</span>
            <h3 className="mt-4 font-black uppercase text-slate-950 text-xl">The Custom Blueprint</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">
              The exact GoHighLevel workflows, triggers, and automated messages needed to fix it.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
            <span className="text-5xl font-black text-blue-600 font-mono">04</span>
            <h3 className="mt-4 font-black uppercase text-slate-950 text-xl">Your Clear Action Plan</h3>
            <p className="mt-3 text-base text-slate-600 leading-relaxed">
              A transparent roadmap you can hire us to build or have your internal team implement.
            </p>
          </div>
        </div>
      </section>

      {/* ==================== SECTION 9: THE ANTI-PITCH POLICY (SOFT GREY) ==================== */}
      <section className="bg-[#F8FAFC] px-6 py-28 text-center text-slate-900 border-y border-slate-200">
        <h2 className="mx-auto max-w-5xl text-4xl font-black uppercase md:text-5xl lg:text-6xl text-slate-950">
          This isn't a <span className="text-blue-600">"get you on Zoom and hard-close you"</span> call.
        </h2>

        <div className="mx-auto mt-8 max-w-3xl space-y-2 text-xl sm:text-2xl text-slate-700 leading-relaxed font-medium">
          <p className="mb-4">I'm not interested in selling you bloated software or services you don't need.</p>
          <p>We'll look at your business.</p>
          <p>We'll identify what's working in your pipeline.</p>
          <p>We'll identify where revenue is slipping through the cracks.</p>
          <p>And we'll map out the exact architecture I'd build next.</p>
          <p className="pt-4 font-bold text-slate-900">
            If Ariyx Systems is the right partner to engineer it for you, I'll show you how we work. If we aren't the best fit, I'll tell you honestly.
          </p>
        </div>

        <p className="mt-10 text-2xl sm:text-3xl font-black text-slate-950">
          EITHER WAY, YOU LEAVE WITH A CUSTOM ARCHITECTURE BLUEPRINT.
        </p>

        <div className="mt-12 flex flex-col items-center gap-3">
          <a
            href={CONTACT.calendlyUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-2xl bg-blue-600 px-10 py-5 text-xl font-extrabold text-white shadow-xl shadow-blue-600/30 transition hover:-translate-y-0.5 hover:brightness-110"
          >
            Claim Your Free Strategy Session →
          </a>
          <p className="text-base text-slate-500">Pick a time that fits your calendar</p>
        </div>
      </section>

      {/* ==================== SECTION 10: WHAT HAPPENS NEXT (MIDNIGHT NAVY) ==================== */}
      <section className="bg-[#101B2D] px-6 py-28 text-center text-white">
        <span className="inline-block rounded-full border border-blue-400/60 bg-blue-500/10 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-white uppercase">
          READY TO PLUG THE LEAKS?
        </span>

        <h2 className="mt-8 text-4xl font-black uppercase md:text-6xl lg:text-7xl text-white">
          Here's what <span className="bg-gradient-to-r from-blue-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">happens next.</span>
        </h2>

        {/* 3 Step Cards — Using Deep Navy #16253D */}
        <div className="mx-auto mt-16 grid max-w-5xl gap-6 text-left md:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8">
            <span className="text-5xl font-black text-blue-400 font-mono">01</span>
            <h3 className="mt-4 font-black uppercase text-white text-xl">Pick Your Time</h3>
            <p className="mt-3 text-slate-200 text-base sm:text-lg leading-relaxed">
              Select a 30-minute slot on the calendar that works best for your schedule.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8">
            <span className="text-5xl font-black text-blue-400 font-mono">02</span>
            <h3 className="mt-4 font-black uppercase text-white text-xl">Tell Us About Your Setup</h3>
            <p className="mt-3 text-slate-200 text-base sm:text-lg leading-relaxed">
              Answer a few quick questions about your business, current CRM, and biggest bottleneck.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#16253D] p-8">
            <span className="text-5xl font-black text-blue-400 font-mono">03</span>
            <h3 className="mt-4 font-black uppercase text-white text-xl">Speak With Emmanuel</h3>
            <p className="mt-3 text-slate-200 text-base sm:text-lg leading-relaxed">
              30 minutes looking directly at your lead flow on screen share and mapping your automated pipeline.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-14 flex flex-col items-center gap-3">
          <a
            href={CONTACT.calendlyUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-2xl bg-blue-600 px-10 py-5 text-xl font-extrabold text-white shadow-xl shadow-blue-600/30 transition hover:-translate-y-0.5 hover:brightness-110"
          >
            YES, BOOK MY FREE STRATEGY SESSION →
          </a>
          <p className="text-base text-slate-300">
            No sales pressure. No generic slides. Just an honest, high-value engineering audit.
          </p>
        </div>
      </section>

      {/* ==================== SECTION 11: FAQ (WHITE) ==================== */}
      <section className="bg-white px-6 py-28 text-slate-900">
        <div className="mx-auto grid max-w-6xl gap-14 md:grid-cols-[1fr_1.4fr] items-start">
          
          {/* Left Column */}
          <div>
            <span className="inline-block rounded-full border border-blue-600/30 bg-blue-50 px-6 py-2 text-xs sm:text-sm font-bold tracking-[0.22em] text-blue-600 uppercase">
              FREQUENTLY ANSWERED QUESTIONS
            </span>
            <h2 className="mt-6 text-4xl font-black md:text-5xl lg:text-6xl text-slate-950 uppercase leading-tight">
              Common Questions, <br />
              <span className="text-blue-600">Answered Plainly</span>
            </h2>
            <p className="mt-6 text-xl text-slate-600 leading-relaxed font-medium">
              Everything you need to know about how the strategy call works and what to expect.
            </p>
            <a
              href={CONTACT.calendlyUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-8 inline-block rounded-xl bg-blue-600 px-8 py-4 text-lg font-extrabold text-white hover:brightness-110 transition"
            >
              Book Your Session
            </a>
          </div>

          {/* Right Column: Accordion */}
          <div className="divide-y divide-slate-200 rounded-3xl border border-slate-200 bg-white overflow-hidden shadow-sm">
            {FAQS.map((faq, idx) => {
              const isOpen = openFaqIdx === idx;
              return (
                <button
                  key={idx}
                  onClick={() => setOpenFaqIdx(isOpen ? -1 : idx)}
                  className="block w-full p-8 text-left hover:bg-slate-50 transition cursor-pointer"
                  aria-expanded={isOpen}
                >
                  <div className="flex justify-between items-center gap-4 font-black text-slate-950 text-xl sm:text-2xl">
                    <span>{faq.q}</span>
                    <span className="text-blue-600 text-3xl font-mono shrink-0">
                      {isOpen ? "−" : "+"}
                    </span>
                  </div>
                  {isOpen && (
                    <p className="mt-4 text-slate-600 text-lg sm:text-xl leading-relaxed font-normal">
                      {faq.a}
                    </p>
                  )}
                </button>
              );
            })}
          </div>

        </div>
      </section>

      {/* ==================== FOOTER (MIDNIGHT NAVY #101B2D) ==================== */}
      <footer className="bg-[#101B2D] px-6 py-14 text-white border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-8 md:flex-row">
          <Link to="/growth" className="focus:outline-none">
            <Logo size="md" />
          </Link>

          <div className="flex flex-wrap items-center justify-center gap-8 text-base font-semibold text-slate-300">
            <a href={`mailto:${CONTACT.email}`} className="hover:text-white transition">
              {CONTACT.email}
            </a>
            <a href={CONTACT.whatsappUrl} target="_blank" rel="noreferrer" className="hover:text-white transition">
              WhatsApp Chat
            </a>
            <a href={CONTACT.calendlyUrl} target="_blank" rel="noreferrer" className="hover:text-white transition">
              Book a Call
            </a>
            <Link to="/" className="text-blue-400 hover:underline transition">
              Explore Full Website →
            </Link>
          </div>

          <p className="text-sm text-slate-400 opacity-70">
            © {new Date().getFullYear()} Ariyx Systems. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Modals */}
      <VideoModal
        isOpen={isVideoOpen}
        onClose={() => setIsVideoOpen(false)}
        videoSrc={VIDEO_TESTIMONIAL.src}
        poster={VIDEO_TESTIMONIAL.poster}
        title={`${VIDEO_TESTIMONIAL.client} (${VIDEO_TESTIMONIAL.business})`}
      />

      <ProjectModal
        project={selectedProject}
        onClose={() => setSelectedProject(null)}
      />
    </div>
  );
}
