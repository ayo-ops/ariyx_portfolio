import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Menu,
  X,
  ArrowRight,
  ArrowUpRight,
  Terminal,
  Mail,
  Link as LinkIcon,
  Briefcase,
  Globe,
  Filter,
  Database,
  Workflow,
  Webhook,
  Bot,
  UserPlus,
  Inbox,
  Send,
  Calendar,
  Users,
  Zap,
  CheckCircle2,
  Star,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Target,
  Brain,
  TrendingUp,
  Code2,
  ExternalLink,
  Play,
  MessageCircle,
} from "lucide-react";

/* ============================================================
   1. EDIT YOUR PROJECTS HERE — add as many as you want.
   Drop screenshots in /public/projects/ using matching filenames.
   ============================================================ */
// const PROJECTS = [
//   {
//     id: 1,
//     name: "[PROJECT NAME]",
//     industry: "[Industry, e.g. Roofing]",
//     description: "[SHORT DESCRIPTION of what you built and the outcome]",
//     services: ["Website Design", "GoHighLevel", "Funnel"],
//     image: "/projects/project-1.jpg",
//     url: "#",
//   },
//   {
//     id: 2,
//     name: "[PROJECT NAME]",
//     industry: "[Industry, e.g. HVAC]",
//     description: "[SHORT DESCRIPTION of what you built and the outcome]",
//     services: ["Website", "Landing Page", "CRM"],
//     image: "/projects/project-2.jpg",
//     url: "#",
//   },
//   {
//     id: 3,
//     name: "[PROJECT NAME]",
//     industry: "[Industry, e.g. Plumbing]",
//     description: "[SHORT DESCRIPTION of what you built and the outcome]",
//     services: ["Website", "Funnel", "Automation"],
//     image: "/projects/project-3.jpg",
//     url: "#",
//   },
//   {
//     id: 4,
//     name: "[PROJECT NAME]",
//     industry: "[Industry, e.g. Electrical]",
//     description: "[SHORT DESCRIPTION of what you built and the outcome]",
//     services: ["Website", "GHL", "Lead Capture"],
//     image: "/projects/project-4.jpg",
//     url: "#",
//   },
//   {
//     id: 5,
//     name: "[PROJECT NAME]",
//     industry: "[Industry, e.g. Cleaning]",
//     description: "[SHORT DESCRIPTION of what you built and the outcome]",
//     services: ["Website", "CRM", "Automation"],
//     image: "/projects/project-5.jpg",
//     url: "#",
//   },
//   {
//     id: 6,
//     name: "[PROJECT NAME]",
//     industry: "[Industry, e.g. Real Estate]",
//     description: "[SHORT DESCRIPTION of what you built and the outcome]",
//     services: ["Website", "Funnel", "Integration"],
//     image: "/projects/project-6.jpg",
//     url: "#",
//   },
//   // Add project 7, 8, 9... following the same shape. The showcase
//   // below automatically handles any number of entries.
// ];

const PROJECTS = [
  {
    id: 1,
    name: "Franchise Fuel",
    industry: "Marketing SaaS",
    description: "A comprehensive revenue compounding system for franchises, featuring automated lead capture, voice AI integration, and multi-location reporting.",
    services: ["Website Design", "GoHighLevel", "SaaS"],
    image: "/projects/mockup-1.png",
    url: "https://franchisefuel.rocks",
  },
  {
    id: 2,
    name: "Wallstreet Realty",
    industry: "Real Estate & Mortgage",
    description: "A full-service brokerage platform with integrated IDX home search, mortgage calculators, and dedicated portals for both buyers and agents.",
    services: ["Website Design", "IDX Integration", "Real Estate"],
    image: "/projects/mockup-2.png",
    url: "https://wallstrealty.com",
  },
  {
    id: 3,
    name: "Clear Inner Focus",
    industry: "Coaching & Leadership",
    description: "A professional coaching and certification website built on the Inner Leadership Method™, featuring booking integrations and client success tracking.",
    services: ["Website Design", "Coaching", "Lead Generation"],
    image: "/projects/mockup-3.png",
    url: "https://clearinnerfocus.com",
  },
  {
    id: 4,
    name: "Health Flow Digital",
    industry: "Healthcare & Automation",
    description: "A HIPAA-compliant marketing and operations platform for healthcare providers, streamlining patient engagement and revenue cycle management.",
    services: ["SaaS Design", "Healthcare", "HIPAA Compliance"],
    image: "/projects/mockup-4.png",
    url: "https://healthflowdigital.com",
  },
  {
    id: 5,
    name: "Rastegar Capital",
    industry: "Finance & Real Estate",
    description: "A high-end investment landing page for a billion-dollar real estate firm, optimized for lead capture and investor relations.",
    services: ["Funnel Design", "Real Estate", "Finance"],
    image: "/projects/mockup-5.png",
    url: "https://crm.industryft.com/v2/preview/y8If3lmovoAbD7xMLfRI",
  },
  {
    id: 6,
    name: "Yoga Brand Builders",
    industry: "Wellness & Business Coaching",
    description: "An automated funnel system for yoga entrepreneurs, designed to sell classes, retreats, and memberships on autopilot.",
    services: ["Funnel Design", "Wellness", "Lead Gen"],
    image: "/projects/mockup-6.png",
    url: "https://yogabrandbuilders.com",
  },
  {
    id: 7,
    name: "Center for Digital Churches",
    industry: "Church Management & SaaS",
    description: "An all-in-one digital growth platform for religious organizations, featuring member portals, custom builders, and automated communication.",
    services: ["SaaS Design", "Church Management", "GoHighLevel"],
    image: "/projects/mockup-7.png",
    url: "https://app.gohighlevel.com/v2/preview/AsKWcZ5Galg3DWl8kLZM?notrack=true",
  },
  {
    id: 8,
    name: "JPK9 Academy",
    industry: "Pet Services & Training",
    description: "A high-impact direct-response funnel for a premier dog training academy, focused on consultation bookings and lead generation.",
    services: ["Funnel Design", "Pet Services", "Lead Gen"],
    image: "/projects/mockup-8.png",
    url: "https://train.jpk9academy.com",
  },
  {
    id: 9,
    name: "Amplify",
    industry: "Personal Branding & Coaching",
    description: "A modern membership platform for personal brand development, featuring waitlist management and community-driven engagement systems.",
    services: ["Website Design", "Membership", "Personal Branding"],
    image: "/projects/mockup-9.png",
    url: "https://app.brandmeon.com/v2/preview/qJzyutWJ2iOXoG9OAw1T?notrack=true",
  },
  {
    id: 10,
    name: "Anchor Identity Workshop",
    industry: "Professional Development",
    description: "A clinically-informed event landing page for professional workshops, featuring a structured registration flow and digital resource delivery.",
    services: ["Event Funnel", "Professional Development", "Lead Gen"],
    image: "/projects/mockup-10.png",
    url: "https://aldigitalintelligencegroup.com/anchor-identity-workshop",
  },
];


/* ============================================================
   2. EDIT YOUR TESTIMONIALS HERE — replace with real reviews.
   Leave the array empty ( [] ) to hide the section entirely.
   ============================================================ */
const TESTIMONIALS = [
  {
    id: 1,
    name: "Marcus Reed",
    business: "Home Service Business",
    review:
      "Ayomide completely transformed the way we handle our leads. The CRM, follow-up workflows, and booking process are now connected and much easier for our team to manage.",
    rating: 5,
  },
  {
    id: 2,
    name: "Danielle Brook",
    business: "Marketing Agency",
    review:
      "The website came out exactly how we wanted it. Beyond the design, Ayomide made sure the forms, CRM, and follow-up process were all connected properly.",
    rating: 5,
  },
  {
    id: 3,
    name: "Ryan Mitchell",
    business: "Roofing Company",
    review:
      "Very knowledgeable with GoHighLevel. He understood what we were trying to build and was able to turn the idea into a working system without making things unnecessarily complicated.",
    rating: 5,
  },
   {
    id: 4,
    name: "Sarah Coleman",
    business: "HVAC Company",
    review:
      "Ayomide was great to work with from start to finish. He was responsive, understood the technical requirements, and made sure everything was tested before delivery.",
    rating: 5,
  },
  {
    id: 5,
    name: "Michael Turner",
    business: "Digital Agency",
    review:
      "What impressed me most was that he didn't just build what we asked for. He actually looked at the whole customer journey and suggested ways to make the system work better.",
    rating: 5,
  },
   {
    id: 6,
    name: "Jessica Morgan",
    business: "Cleaning Services",
    review:
      "Our lead management process is much more organized now. Leads are captured, followed up with, and moved through the pipeline automatically instead of relying on manual work.",
    rating: 5,
  },
  {
    id: 7,
    name: "Daniel Carter",
    business: "Consulting Business",
    review:
      "Ayomide knows both the technical and business side of automation. He explained everything clearly and built a system that our team could actually understand and use.",
    rating: 5,
  },
   {
    id: 8,
    name: "Lauren Hayes",
    business: "Home Remodeling Company",
    review:
      "The funnel and automation setup saved us a huge amount of time. Everything from the initial form submission to appointment follow-up is much more streamlined.",
    rating: 5,
  },
  {
    id: 9,
    name: "Chris Anderson",
    business: "SaaS Consultant",
    review:
      "Professional, reliable, and very easy to communicate with. Ayomide took the time to understand the project instead of rushing straight into the build.",
    rating: 5,
  },
  {
    id: 10,
    name: "[CLIENT NAME]",
    business: "[CLIENT BUSINESS / INDUSTRY]",
    review:
      "[REPLACE WITH A SPECIFIC, PERMISSIONED CLIENT QUOTE THAT MENTIONS THE PROBLEM, THE WORK, OR THE RESULT.]",
    rating: 5,
  },
  {
    id: 11,
    name: "Olivia Bennett",
    business: "Plumbing Company",
    review:
      "Great experience overall. He handled the website, CRM setup, workflows, and integrations as one complete system, which was exactly what we needed.",
    rating: 5,
  },
];

/* ============================================================
   3. EDIT YOUR CONTACT LINKS AND PORTRAIT HERE
   ============================================================ */
const CONTACT = {
  email: "ariyoleke232@gmail.com",
  linkedin: "https://www.linkedin.com/in/ariyo-emmanuel/",
  upwork: "https://www.upwork.com/freelancers/~01ca944a52609188c9?mp_source=share",
};
const PORTRAIT_IMAGE = "/portrait.jpeg";
// Real booking link — primary CTAs point here so a click goes straight
// to your calendar instead of asking someone to open their email app.
const CALENDLY_URL = "https://calendly.com/ariyoleke232/30min";
// WhatsApp number in international format, no spaces, no "+".
const WHATSAPP_NUMBER = "2349152581764";
const WHATSAPP_URL = `https://wa.me/${WHATSAPP_NUMBER}`;

/* ============================================================
   4. OPTIONAL VIDEO TESTIMONIAL — place the client video here.
   Replace src and poster with files in /public/testimonials/.
   This card is rendered immediately below the hero so proof appears
   before visitors reach the longer service sections.
   ============================================================ */
const VIDEO_TESTIMONIAL = {
  src: "/testimonials/client-testimonial.mp4",
  poster: "/testimonials/client-testimonial-poster.jpg",
  client: "Patty Jackson",
  business: "Clear Inner Focus — Life Coaching & Coach Certification",
  caption: "Patty appreciated the GoHighLevel automation setup, including her lead capture form, lead magnet delivery, and automated email follow-up sequences.",
};
// Your logo mark — drop the file in /public/ and point this to it.
// If it fails to load (or isn't there yet), the terminal icon shows instead.
const LOGO_IMAGE = "/logo.png";
const BRAND_NAME = "ARIYX";
const BRAND_LAST = "SYSTEMS";

const SERVICES = [
  {
    icon: Globe,
    title: "GoHighLevel Websites",
    description:
      "Custom-built, fast-loading websites on GoHighLevel, designed to convert visitors into leads.",
    detail: "Mobile-first builds, custom sections, speed-optimized delivery.",
    color: "teal",
  },
  {
    icon: Filter,
    title: "Landing Pages & Funnels",
    description:
      "Multi-step funnels and landing pages built to guide a visitor toward a single, clear action.",
    detail: "Split-testable structure, clear CTAs, conversion-first layout.",
    color: "blue",
  },
  {
    icon: Database,
    title: "CRM Setup & Optimization",
    description:
      "Pipelines, custom fields, and tagging structured so your team always knows where a lead stands.",
    detail: "Custom pipelines, tagging logic, clean data structure.",
    color: "violet",
  },
  {
    icon: Workflow,
    title: "Workflow Automation",
    description:
      "Automated sequences that follow up, qualify, and move leads forward without manual work.",
    detail: "SMS/email sequences, task routing, conditional logic.",
    color: "amber",
  },
  {
    icon: Webhook,
    title: "API & Webhook Integrations",
    description:
      "Connecting GoHighLevel to the other tools in your stack, so data moves without gaps.",
    detail: "Two-way syncs, custom endpoints, third-party tool bridges.",
    color: "rose",
  },
  {
    icon: Bot,
    title: "AI & Lead Follow-Up Automation",
    description:
      "AI-assisted responses and follow-up that keep leads engaged in the minutes after they convert.",
    detail: "Instant response bots, smart routing, AI-assisted replies.",
    color: "emerald",
  },
];

const SYSTEM_NODES = [
  { icon: Globe, label: "Website", desc: "A fast, conversion-focused site that turns visitors into leads.", color: "teal" },
  { icon: Inbox, label: "Lead Capture", desc: "Forms and funnels that capture the right details the first time.", color: "blue" },
  { icon: Database, label: "CRM", desc: "Every lead organized, tagged, and tracked in one clean pipeline.", color: "violet" },
  { icon: Workflow, label: "Automation", desc: "Workflows that qualify and route leads without manual work.", color: "amber" },
  { icon: Send, label: "Follow-Up", desc: "SMS and email sequences that keep leads engaged automatically.", color: "rose" },
  { icon: Calendar, label: "Booking", desc: "Appointments land directly on the calendar, no back-and-forth.", color: "emerald" },
  { icon: Users, label: "Sales", desc: "Your team picks up a warm, qualified lead that's ready to close.", color: "teal" },
];

const CAPABILITIES = [
  { icon: Target, title: "Conversion Focused", desc: "Every page is built to move a visitor toward one clear action.", color: "teal" },
  { icon: Brain, title: "Systems Thinker", desc: "I design the full path a lead takes, not just the page they land on.", color: "blue" },
  { icon: Zap, title: "Automation Expert", desc: "Follow-up and routing happen automatically, without manual work.", color: "amber" },
  { icon: TrendingUp, title: "Results Driven", desc: "Practical builds that are easy for your team to manage and measure.", color: "violet" },
];

const TECH_STACK = [
  "GoHighLevel",
  "n8n",
  "WordPress",
  "React",
  "JavaScript",
  "REST APIs",
  "Webhooks",
  "CRM Pipelines",
  "Workflow Automation",
  "AI Follow-Up",
];

const PROCESS_STEPS = [
  { num: "01", title: "Understand", desc: "I learn how leads currently move through your business and where they stall." },
  { num: "02", title: "Plan", desc: "I map the website, CRM, and automation structure before writing a line of code." },
  { num: "03", title: "Build", desc: "The website, funnel, and CRM pipeline get built to that plan." },
  { num: "04", title: "Automate", desc: "Follow-up, tagging, and routing get wired in so leads are never missed." },
  { num: "05", title: "Optimize", desc: "I review performance and refine what's not converting." },
];

const INDUSTRIES = [
  "Roofing",
  "HVAC",
  "Plumbing",
  "Electrical",
  "Cleaning",
  "Landscaping",
  "Home Remodeling",
  "Real Estate",
];

const STATS = [
  { end: 5, suffix: "+", label: "Years of GoHighLevel Experience" },
  { end: 57, suffix: "+", label: "Recent Websites Built" },
  { end: 0, suffix: "", label: "CRM & Automation Systems", isText: true, text: "CRM & Automation" },
];

const NAV_LINKS = [
  { label: "Work", href: "#work" },
  { label: "Services", href: "#services" },
  { label: "Systems", href: "#systems" },
  { label: "Reviews", href: "#reviews" },
  { label: "Contact", href: "#contact" },
];

const FOOTER_LINKS = [
  { label: "Home", href: "#top" },
  { label: "Work", href: "#work" },
  { label: "Services", href: "#services" },
  { label: "Systems", href: "#systems" },
  { label: "Reviews", href: "#reviews" },
  { label: "About", href: "#about" },
  { label: "Contact", href: "#contact" },
];

/* ---------- Accent color system (card color variety) ---------- */
const ACCENTS = {
  teal:    { text: "text-teal-300",    bg: "bg-teal-400/[0.1]",    border: "border-teal-400/30",    glow: "shadow-[0_0_30px_-10px_rgba(45,217,197,0.45)]",  dot: "bg-teal-400" },
  blue:    { text: "text-blue-300",    bg: "bg-blue-400/[0.1]",    border: "border-blue-400/30",    glow: "shadow-[0_0_30px_-10px_rgba(96,165,250,0.45)]",  dot: "bg-blue-400" },
  violet:  { text: "text-violet-300",  bg: "bg-violet-400/[0.1]",  border: "border-violet-400/30",  glow: "shadow-[0_0_30px_-10px_rgba(167,139,250,0.45)]", dot: "bg-violet-400" },
  amber:   { text: "text-amber-300",   bg: "bg-amber-400/[0.1]",   border: "border-amber-400/30",   glow: "shadow-[0_0_30px_-10px_rgba(251,191,36,0.45)]",  dot: "bg-amber-400" },
  rose:    { text: "text-rose-300",    bg: "bg-rose-400/[0.1]",    border: "border-rose-400/30",    glow: "shadow-[0_0_30px_-10px_rgba(251,113,133,0.45)]", dot: "bg-rose-400" },
  emerald: { text: "text-emerald-300", bg: "bg-emerald-400/[0.1]", border: "border-emerald-400/30", glow: "shadow-[0_0_30px_-10px_rgba(52,211,153,0.45)]",  dot: "bg-emerald-400" },
};

/* ---------- Scroll reveal hook ---------- */
function useReveal(threshold = 0.15) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.unobserve(el);
        }
      },
      { threshold }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return [ref, visible];
}

function Reveal({ children, className = "", delay = 0, as: Tag = "div" }) {
  const [ref, visible] = useReveal();
  return (
    <Tag
      ref={ref}
      className={`transition-all duration-700 ease-out ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
      } ${className}`}
      style={{ transitionDelay: visible ? `${delay}ms` : "0ms" }}
    >
      {children}
    </Tag>
  );
}

/* ---------- Count-up number ---------- */
function useCountUp(end, trigger, duration = 1600) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!trigger) return;
    let raf;
    let start;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [trigger, end, duration]);
  return count;
}

function StatBlock({ stat, delay }) {
  const [ref, visible] = useReveal(0.4);
  const count = useCountUp(stat.end, visible);
  return (
    <Reveal delay={delay}>
      <div ref={ref} className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-8 hover:border-teal-400/30 transition-colors duration-300">
        {stat.isText ? (
          <div className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white leading-tight">
            {stat.text}
            <br />
            Systems
          </div>
        ) : (
          <div className="font-[Space_Grotesk,sans-serif] text-6xl md:text-7xl font-medium grad-text">
            {count}
            {stat.suffix}
          </div>
        )}
        <div className="mt-3 text-white/60 text-xl">{stat.label}</div>
      </div>
    </Reveal>
  );
}

/* ---------- Logo mark (falls back to icon if no logo image yet) ---------- */
function LogoMark({ className = "w-5 h-5" }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <Terminal className={`${className} text-teal-400`} strokeWidth={2} />;
  return (
    <img
      src={LOGO_IMAGE}
      alt={`${BRAND_NAME} ${BRAND_LAST} logo`}
      onError={() => setFailed(true)}
      className={`${className} object-contain`}
    />
  );
}

/* ---------- Eyebrow ---------- */
function Eyebrow({ index, children }) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <span className="font-mono text-lg tracking-[0.15em] text-teal-400">{index}</span>
      <span className="h-px w-10 bg-gradient-to-r from-teal-400/60 to-transparent" />
      <span className="font-mono text-lg tracking-[0.15em] text-white/60 uppercase">{children}</span>
    </div>
  );
}

/* ---------- Image with graceful placeholder fallback ---------- */
function SmartImage({ src, alt, className = "" }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-[#0F1B24] to-[#0A0E14] ${className}`}>
        <div className="text-center px-4">
          <Globe className="w-9 h-9 text-teal-400/30 mx-auto mb-3" strokeWidth={1.5} />
          <span className="font-mono text-base tracking-wide text-white/25">{src}</span>
        </div>
      </div>
    );
  }
  return <img src={src} alt={alt} onError={() => setFailed(true)} className={className} />;
}

/* ---------- Video testimonial placeholder ---------- */
function VideoTestimonialCard() {
  return (
    <section aria-label="Client video testimonial" className="border-y border-white/[0.06] bg-[#0B111A] px-6 md:px-8 py-8">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-5 md:gap-8">
        <a
          href={VIDEO_TESTIMONIAL.src}
          target="_blank"
          rel="noreferrer"
          className="group relative w-full md:w-72 aspect-video shrink-0 overflow-hidden rounded-xl border border-teal-400/25 bg-[#0A0E14] hover:border-teal-400/60 transition-colors"
          aria-label={`Play video testimonial from ${VIDEO_TESTIMONIAL.client}`}
        >
          <SmartImage
            src={VIDEO_TESTIMONIAL.poster}
            alt={`Video testimonial from ${VIDEO_TESTIMONIAL.client}`}
            className="w-full h-full object-cover opacity-75 group-hover:opacity-100 transition-opacity"
          />
          <span className="absolute inset-0 flex items-center justify-center bg-[#0A0E14]/25 group-hover:bg-[#0A0E14]/10 transition-colors">
            <span className="w-12 h-12 rounded-full bg-teal-400 text-[#0A0E14] flex items-center justify-center shadow-[0_0_30px_-6px_rgba(45,217,197,0.8)]">
              <Play className="w-5 h-5 ml-0.5 fill-current" />
            </span>
          </span>
          <span className="absolute left-3 top-3 rounded-full border border-teal-400/30 bg-[#0B121B]/90 px-2.5 py-1 font-mono text-[11px] tracking-wider text-teal-300">
            VIDEO TESTIMONIAL
          </span>
        </a>
        <div>
          <p className="font-mono text-sm tracking-[0.18em] text-teal-300/80 uppercase">Client proof</p>
          <h2 className="mt-2 font-[Space_Grotesk,sans-serif] text-2xl md:text-3xl text-white font-medium">Hear what the build changed for a real client.</h2>
          <p className="mt-2 text-lg text-white/55 max-w-2xl">{VIDEO_TESTIMONIAL.caption}</p>
          <p className="mt-3 font-mono text-sm text-white/40">{VIDEO_TESTIMONIAL.client} · {VIDEO_TESTIMONIAL.business}</p>
      
        </div>
      </div>
    </section>
  );
}

/* ---------- Marquee ---------- */
function IndustriesMarquee() {
  const loop = [...INDUSTRIES, ...INDUSTRIES];
  return (
    <div className="border-y border-white/[0.06] bg-[#0B111A] py-10 overflow-hidden">
      <div className="max-w-6xl mx-auto px-6 md:px-8 mb-8 text-center">
        <span className="font-mono text-xl tracking-[0.25em] text-white/65">
          BUILDING SYSTEMS FOR SERVICE BUSINESSES
        </span>
      </div>
      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-[#0B111A] to-transparent z-10" />
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-[#0B111A] to-transparent z-10" />
        <div className="flex gap-4 animate-marquee w-max">
          {loop.map((industry, i) => (
            <div
              key={i}
              className="flex items-center gap-2.5 rounded-full border border-white/[0.08] px-6 py-3 shrink-0"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
              <span className="text-white/60 text-xl whitespace-nowrap">{industry}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------- Floating badge for hero ---------- */
function FloatingBadge({ icon: Icon, label, className = "", delay = "0s", duration = "6s" }) {
  return (
    <div
      className={`absolute flex items-center gap-2 rounded-xl border border-teal-400/25 bg-[#0B121B]/95 backdrop-blur-sm px-4 py-2.5 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.6)] ${className}`}
      style={{ animation: `float ${duration} ease-in-out infinite`, animationDelay: delay }}
    >
      <Icon className="w-4 h-4 text-teal-400 shrink-0" />
      <span className="font-mono text-base text-white/80 whitespace-nowrap">{label}</span>
    </div>
  );
}

/* ---------- Hero dashboard visual ---------- */
function HeroVisual() {
  return (
    <div className="relative w-full h-[440px] sm:h-[500px] lg:h-[560px]">
      <div
        className="pointer-events-none absolute inset-0 rounded-full opacity-40 blur-3xl"
        style={{ background: "radial-gradient(circle at 50% 50%, #2CD9C5 0%, transparent 60%)" }}
      />

      {/* connection lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 500 500" fill="none">
        <line x1="250" y1="250" x2="70" y2="90" stroke="#2CD9C5" strokeOpacity="0.35" strokeWidth="1.5" strokeDasharray="5 6" className="dash-flow" />
        <line x1="250" y1="250" x2="430" y2="80" stroke="#2CD9C5" strokeOpacity="0.35" strokeWidth="1.5" strokeDasharray="5 6" className="dash-flow" />
        <line x1="250" y1="250" x2="60" y2="400" stroke="#2CD9C5" strokeOpacity="0.35" strokeWidth="1.5" strokeDasharray="5 6" className="dash-flow" />
        <line x1="250" y1="250" x2="440" y2="420" stroke="#2CD9C5" strokeOpacity="0.35" strokeWidth="1.5" strokeDasharray="5 6" className="dash-flow" />
      </svg>

      {/* center dashboard card */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[280px] sm:w-[320px] rounded-2xl border border-teal-400/25 bg-[#0B121B]/95 backdrop-blur-sm shadow-[0_0_70px_-15px_rgba(45,217,197,0.4)] overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-3.5 border-b border-white/[0.07]">
          <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
          <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
          <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
          <span className="ml-3 font-mono text-[11px] text-white/30">crm.dashboard</span>
        </div>
        <div className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-mono text-base text-white/60">Lead Pipeline</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-teal-300">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
              Live
            </span>
          </div>
          {[
            { label: "New Leads", value: 82, icon: UserPlus },
            { label: "CRM Synced", value: 100, icon: Database },
            { label: "Follow-Up Sent", value: 67, icon: Send },
          ].map((row, i) => {
            const Icon = row.icon;
            return (
              <div key={row.label}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="flex items-center gap-2 text-lg text-white/60">
                    <Icon className="w-3.5 h-3.5 text-teal-400" strokeWidth={2} />
                    {row.label}
                  </span>
                  <span className="font-mono text-base text-white/60">{row.value}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-300"
                    style={{ width: `${row.value}%`, animation: `grow 1.4s ease-out ${i * 150 + 200}ms forwards`, transform: "scaleX(0)", transformOrigin: "left" }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <FloatingBadge icon={UserPlus} label="New Lead" className="top-2 left-0 sm:left-4" delay="0s" duration="7s" />
      <FloatingBadge icon={Zap} label="Automation Triggered" className="top-0 right-0 sm:right-2" delay="1.2s" duration="8s" />
      <FloatingBadge icon={Calendar} label="Appointment Booked" className="bottom-4 left-0" delay="0.6s" duration="6.5s" />
      <FloatingBadge icon={Send} label="Follow-up Sent" className="bottom-0 right-0 sm:right-4" delay="1.8s" duration="7.5s" />
    </div>
  );
}

/* ---------- Capability card ---------- */
function CapabilityCard({ cap, delay }) {
  const Icon = cap.icon;
  const a = ACCENTS[cap.color] || ACCENTS.teal;
  return (
    <Reveal delay={delay}>
      <div className="group rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6 hover:border-white/[0.16] hover:bg-white/[0.03] hover:-translate-y-1 transition-all duration-300">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center border ${a.border} ${a.bg} mb-4 group-hover:scale-110 transition-transform duration-300`}>
          <Icon className={`w-5 h-5 ${a.text}`} strokeWidth={1.8} />
        </div>
        <h4 className="font-[Space_Grotesk,sans-serif] text-2xl text-white font-medium mb-1.5">{cap.title}</h4>
        <p className="text-lg text-white/60 leading-relaxed">{cap.desc}</p>
      </div>
    </Reveal>
  );
}

/* ---------- Featured Work ---------- */
function FeaturedWork({ onOpenModal }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const active = PROJECTS[index];
  const hasMultipleProjects = PROJECTS.length > 1;

  useEffect(() => {
    if (paused || !hasMultipleProjects) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % PROJECTS.length), 5500);
    return () => clearInterval(id);
  }, [paused, hasMultipleProjects]);

  const showPrevious = () => setIndex((i) => (i - 1 + PROJECTS.length) % PROJECTS.length);
  const showNext = () => setIndex((i) => (i + 1) % PROJECTS.length);

  return (
    <div className="relative" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <Reveal>
        <div className="relative rounded-[1.35rem] border border-white/[0.12] bg-[#070B10] p-2 sm:p-3 shadow-[0_30px_90px_-35px_rgba(0,0,0,0.9)]">
          <div className="flex items-center gap-2 rounded-t-xl border border-white/[0.07] border-b-0 bg-[#111923] px-4 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-300/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-teal-300/80" />
            <span className="ml-3 hidden flex-1 rounded-md border border-white/[0.08] bg-[#0A0E14] px-3 py-1 font-mono text-xs text-white/30 sm:block">
              {active.url && active.url !== "#" ? active.url.replace(/^https?:\/\//, "") : "your-project-url.com"}
            </span>
            <span className="ml-auto font-mono text-xs tracking-widest text-teal-300/70">CASE STUDY {String(index + 1).padStart(2, "0")}</span>
          </div>

          <div key={active.id} className="relative aspect-[16/9] overflow-hidden rounded-b-xl border border-white/[0.07] bg-[#0B111A]" style={{ animation: "projectSlide 700ms cubic-bezier(0.22,1,0.36,1)" }}>
            <SmartImage src={active.image} alt={`${active.name} project mockup`} className="h-full w-full object-cover" />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#05070A]/45 via-transparent to-transparent" />
            {hasMultipleProjects && (
              <>
                <button type="button" onClick={showPrevious} aria-label="View previous case study" className="absolute left-4 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-[#0A0E14]/75 text-white/80 backdrop-blur-sm transition-all hover:border-teal-300/60 hover:bg-[#0A0E14] hover:text-teal-300 sm:h-11 sm:w-11">
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button type="button" onClick={showNext} aria-label="View next case study" className="absolute right-4 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-[#0A0E14]/75 text-white/80 backdrop-blur-sm transition-all hover:border-teal-300/60 hover:bg-[#0A0E14] hover:text-teal-300 sm:h-11 sm:w-11">
                  <ChevronRight className="h-5 w-5" />
                </button>
              </>
            )}
          </div>
        </div>

        <div className="mt-7 grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="mb-3 flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm tracking-[0.18em] text-teal-300 uppercase">{active.industry}</span>
              <span className="h-1 w-1 rounded-full bg-white/25" />
              <span className="font-mono text-sm text-white/35">{String(index + 1).padStart(2, "0")} / {String(PROJECTS.length).padStart(2, "0")}</span>
            </div>
            <h3 className="font-[Space_Grotesk,sans-serif] text-3xl font-medium text-white md:text-4xl">{active.name}</h3>
            <p className="mt-4 max-w-3xl text-lg leading-relaxed text-white/60">{active.description}</p>
            <p className="mt-3 max-w-3xl font-mono text-sm leading-relaxed text-white/35"></p>
            <div className="mt-5 flex flex-wrap gap-2">
              {active.services.map((service) => (
                <span key={service} className="rounded-full border border-teal-400/20 bg-teal-400/[0.07] px-3 py-1.5 font-mono text-sm tracking-wide text-teal-300/80">{service}</span>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            {active.url && active.url !== "#" ? (
              <a href={active.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full bg-teal-400 px-6 py-3 font-medium text-[#0A0E14] transition-colors hover:bg-teal-300">
                View Live Site <ExternalLink className="h-4 w-4" />
              </a>
            ) : (
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-400/25 px-6 py-3 font-medium text-teal-300/80">Replace With Live URL <ExternalLink className="h-4 w-4" /></span>
            )}
            <button type="button" onClick={() => onOpenModal(active)} className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3 font-medium text-white/80 transition-colors hover:border-teal-400/50">
              View Details <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {hasMultipleProjects && (
          <div className="mt-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-white/[0.08]" />
            <div className="flex items-center gap-2" aria-label="Case study navigation">
              {PROJECTS.map((project, projectIndex) => (
                <button key={project.id} type="button" onClick={() => setIndex(projectIndex)} aria-label={`View case study ${projectIndex + 1}`} className={`h-1.5 rounded-full transition-all duration-300 ${projectIndex === index ? "w-9 bg-teal-300" : "w-3 bg-white/20 hover:bg-white/40"}`} />
              ))}
            </div>
            <div className="h-px flex-1 bg-white/[0.08]" />
          </div>
        )}
      </Reveal>
    </div>
  );
}

/* ---------- Project detail modal ---------- */
function ProjectModal({ project, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  if (!project) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-8 bg-[#05070A]/85 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-2xl border border-teal-400/25 bg-[#0B111A] shadow-[0_30px_90px_-20px_rgba(0,0,0,0.7)] animate-scaleIn"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-9 h-9 rounded-full flex items-center justify-center border border-white/15 bg-[#0A0E14]/80 text-white/70 hover:text-white hover:border-teal-400/50 transition-colors"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>
        <div className="aspect-[16/9] border-b border-white/[0.08]">
          <SmartImage src={project.image} alt={project.name} className="w-full h-full object-cover" />
        </div>
        <div className="p-8">
          <span className="font-mono text-base tracking-widest text-teal-300 uppercase">{project.industry}</span>
          <h3 className="font-[Space_Grotesk,sans-serif] text-3xl text-white font-medium mt-2 mb-4">
            {project.name}
          </h3>
          <p className="text-white/60 text-lg leading-relaxed mb-6">{project.description}</p>
          <div className="flex flex-wrap gap-2 mb-8">
            {project.services.map((s) => (
              <span key={s} className="rounded-full font-mono text-base tracking-wide text-teal-300/80 bg-teal-400/[0.08] px-3 py-1.5">
                {s}
              </span>
            ))}
          </div>
          {project.url && project.url !== "#" ? (
            <a
              href={project.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-teal-400 text-[#0A0E14] font-medium px-6 py-3 hover:bg-teal-300 transition-colors duration-200"
            >
              Visit Live Site <ExternalLink className="w-4 h-4" />
            </a>
          ) : (
            <span className="inline-flex items-center gap-2 rounded-full border border-teal-400/25 text-teal-300/80 font-medium px-6 py-3">
              Replace With Live URL <ExternalLink className="w-4 h-4" />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------- Service card ---------- */
function ServiceCard({ service, delay }) {
  const Icon = service.icon;
  const a = ACCENTS[service.color] || ACCENTS.teal;
  return (
    <Reveal delay={delay} className="h-full">
      <div className="group relative h-full rounded-2xl border border-white/[0.08] bg-white/[0.015] p-8 overflow-hidden hover:border-white/[0.18] hover:-translate-y-1.5 transition-all duration-300 hover:shadow-[0_20px_50px_-25px_rgba(0,0,0,0.6)]">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${a.border} ${a.bg} mb-6 group-hover:scale-110 transition-all duration-300`}>
          <Icon className={`w-6 h-6 ${a.text}`} strokeWidth={1.6} />
        </div>
        <h3 className="font-[Space_Grotesk,sans-serif] text-3xl text-white font-medium mb-3">{service.title}</h3>
        <p className="text-xl text-white/60 leading-relaxed">{service.description}</p>
        <div className="grid transition-all duration-300 grid-rows-[0fr] group-hover:grid-rows-[1fr]">
          <div className="overflow-hidden">
            <p className={`pt-4 mt-4 border-t border-white/[0.08] text-lg ${a.text}`}>{service.detail}</p>
          </div>
        </div>
      </div>
    </Reveal>
  );
}

/* ---------- System stage card (rebuilt as a content card, not a thin icon row) ---------- */
/* ---------- System flow: a real animated pipeline, not a static card grid ---------- */
function SystemFlow() {
  const [ref, visible] = useReveal(0.2);

  return (
    <div ref={ref}>
      {/* Desktop: horizontal pipeline */}
      <div className="hidden lg:block relative pt-20 pb-2">
        <div className="absolute left-0 right-0 top-20 h-1 rounded-full overflow-hidden bg-gradient-to-r from-teal-400/25 via-violet-400/25 to-emerald-400/25">
          {visible && (
            <>
              <span className="flow-h" style={{ animationDelay: "0s" }} />
              <span className="flow-h" style={{ animationDelay: "1.8s" }} />
            </>
          )}
        </div>

        <div className="flex justify-between gap-4">
          {SYSTEM_NODES.map((node, i) => {
            const Icon = node.icon;
            const a = ACCENTS[node.color] || ACCENTS.teal;
            return (
              <Reveal key={node.label} delay={i * 130} className={`relative flex-1 flex flex-col items-center text-center ${i % 2 === 1 ? "mt-12" : "mt-0"}`}>
                <div
                  className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center border-2 ${a.border} ${a.bg} ${a.glow} hover:scale-110 transition-transform duration-300`}
                  style={visible ? { animation: `nodePulse 3.6s ease-in-out ${i * 0.45}s infinite` } : undefined}
                >
                  <Icon className={`w-8 h-8 ${a.text}`} strokeWidth={1.8} />
                </div>
                <span className="mt-5 font-mono text-base text-white/30">{String(i + 1).padStart(2, "0")}</span>
                <h4 className="mt-1 font-[Space_Grotesk,sans-serif] text-xl text-white font-medium">{node.label}</h4>
                <p className="mt-2 text-lg text-white/50 leading-snug max-w-[170px]">{node.desc}</p>
              </Reveal>
            );
          })}
        </div>
      </div>

      {/* Mobile / tablet: vertical pipeline */}
      <div className="lg:hidden relative pl-4">
        <div className="absolute left-10 top-3 bottom-3 w-1 rounded-full overflow-hidden bg-gradient-to-b from-teal-400/25 via-violet-400/25 to-emerald-400/25">
          {visible && <span className="flow-v" />}
        </div>
        <div className="space-y-11">
          {SYSTEM_NODES.map((node, i) => {
            const Icon = node.icon;
            const a = ACCENTS[node.color] || ACCENTS.teal;
            return (
              <Reveal key={node.label} delay={i * 130} className="relative flex gap-6">
                <div
                  className={`relative z-10 shrink-0 w-20 h-20 rounded-full flex items-center justify-center border-2 ${a.border} ${a.bg} ${a.glow}`}
                  style={visible ? { animation: `nodePulse 3.6s ease-in-out ${i * 0.45}s infinite` } : undefined}
                >
                  <Icon className={`w-8 h-8 ${a.text}`} strokeWidth={1.8} />
                </div>
                <div className="pt-3">
                  <span className="font-mono text-base text-white/30">{String(i + 1).padStart(2, "0")}</span>
                  <h4 className="font-[Space_Grotesk,sans-serif] text-2xl text-white font-medium">{node.label}</h4>
                  <p className="mt-1 text-lg text-white/50 leading-relaxed">{node.desc}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ---------- Testimonial carousel ---------- */
function TestimonialCarousel() {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || TESTIMONIALS.length <= 1) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % TESTIMONIALS.length), 5000);
    return () => clearInterval(id);
  }, [paused]);

  if (TESTIMONIALS.length === 0) return null;

  return (
    <div
      className="relative max-w-3xl mx-auto"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.02]">
        <div
          className="flex transition-transform duration-700 ease-[cubic-bezier(0.65,0,0.35,1)]"
          style={{ transform: `translateX(-${index * 100}%)` }}
        >
          {TESTIMONIALS.map((t) => (
            <div key={t.id} className="w-full shrink-0 p-10 md:p-14 text-center min-h-[280px] flex flex-col items-center justify-center">
              <div className="flex gap-1 mb-6">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`w-5 h-5 ${i < t.rating ? "text-teal-400 fill-teal-400" : "text-white/15"}`}
                  />
                ))}
              </div>
              <p className="text-xl md:text-2xl text-white/80 leading-relaxed font-[Space_Grotesk,sans-serif] font-normal max-w-xl">
                &ldquo;{t.review}&rdquo;
              </p>
              <div className="mt-8">
                <div className="text-white font-medium">{t.name}</div>
                <div className="text-white/60 text-lg font-mono mt-1">{t.business}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {TESTIMONIALS.length > 1 && (
        <>
          <button
            onClick={() => setIndex((i) => (i - 1 + TESTIMONIALS.length) % TESTIMONIALS.length)}
            className="hidden sm:flex absolute left-0 top-1/2 -translate-x-16 -translate-y-1/2 w-11 h-11 rounded-full items-center justify-center border border-white/15 text-white/60 hover:text-teal-300 hover:border-teal-400/40 transition-colors"
            aria-label="Previous testimonial"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIndex((i) => (i + 1) % TESTIMONIALS.length)}
            className="hidden sm:flex absolute right-0 top-1/2 translate-x-16 -translate-y-1/2 w-11 h-11 rounded-full items-center justify-center border border-white/15 text-white/60 hover:text-teal-300 hover:border-teal-400/40 transition-colors"
            aria-label="Next testimonial"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <div className="flex flex-wrap justify-center gap-2 mt-8 max-w-xs mx-auto">
            {TESTIMONIALS.map((_, i) => (
              <button
                key={i}
                onClick={() => setIndex(i)}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === index ? "w-8 bg-teal-400" : "w-1.5 bg-white/20 hover:bg-white/40"
                }`}
                aria-label={`Go to testimonial ${i + 1}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* ============================================================
   MAIN COMPONENT
   ============================================================ */
export default function PortfolioSite() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [modalProject, setModalProject] = useState(null);
  const [ctaGlow, setCtaGlow] = useState({ x: 50, y: 50 });

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const closeMenu = () => setMenuOpen(false);

  const handleCtaMouseMove = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setCtaGlow({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    });
  }, []);

  return (
    <div className="bg-[#0A0E14] text-[#F2F4F7] min-h-screen font-[Inter,sans-serif] antialiased selection:bg-teal-500/30 selection:text-white">
      <style>{`
        html { scroll-behavior: smooth; }
        @keyframes pulseRight {
          0% { left: -6px; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { left: calc(100% - 2px); opacity: 0; }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-12px); }
        }
        @keyframes grow {
          to { transform: scaleX(1); }
        }
        @keyframes gradientShift {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes marquee {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        @keyframes dashFlow {
          to { stroke-dashoffset: -22; }
        }
        @keyframes flowAcross {
          0% { left: -8%; opacity: 0; }
          12% { opacity: 1; }
          88% { opacity: 1; }
          100% { left: 100%; opacity: 0; }
        }
        @keyframes flowDown {
          0% { top: -12%; opacity: 0; }
          12% { opacity: 1; }
          88% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        @keyframes nodePulse {
          0%, 100% { transform: scale(1); filter: brightness(1); }
          50% { transform: scale(1.12); filter: brightness(1.35); }
        }
        .flow-h {
          position: absolute;
          top: 0; bottom: 0;
          width: 90px;
          left: -8%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.95), transparent);
          filter: blur(1px);
          animation: flowAcross 3.6s linear infinite;
        }
        .flow-v {
          position: absolute;
          left: 0; right: 0;
          height: 90px;
          top: -12%;
          background: linear-gradient(180deg, transparent, rgba(255,255,255,0.95), transparent);
          filter: blur(1px);
          animation: flowDown 3.6s linear infinite;
        }
        @keyframes projectSlide {
          from { opacity: 0; transform: translateX(28px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.96) translateY(8px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        .pulse-h { animation: pulseRight 2.6s cubic-bezier(0.4,0,0.2,1) infinite; }
        .dash-flow { animation: dashFlow 1.2s linear infinite; }
        .animate-marquee { animation: marquee 26s linear infinite; }
        .animate-fadeIn { animation: fadeIn 0.2s ease-out; }
        .animate-scaleIn { animation: scaleIn 0.25s ease-out; }
        .grad-text {
          background: linear-gradient(90deg, #2CD9C5, #6FE8DB, #2CD9C5);
          background-size: 200% auto;
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          animation: gradientShift 6s ease infinite;
        }
        .dot-grid {
          background-image:
            linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px),
            radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px);
          background-size: 64px 64px, 64px 64px, 32px 32px;
          background-position: -1px -1px, -1px -1px, -1px -1px;
        }
        @media (prefers-reduced-motion: reduce) {
          .pulse-h, .dash-flow, .animate-marquee, .grad-text, .flow-h, .flow-v, [style*="animation"] { animation: none !important; }
          html { scroll-behavior: auto; }
        }
      `}</style>

      {modalProject && <ProjectModal project={modalProject} onClose={() => setModalProject(null)} />}

      {/* ================= NAV ================= */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled ? "bg-[#0A0E14]/90 backdrop-blur-md border-b border-white/[0.06]" : "bg-transparent border-b border-transparent"
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 md:px-8 h-20 flex items-center justify-between">
          <a href="#top" className="flex items-center gap-1">
            <LogoMark className="w-20 h-20" />
            <span className="font-mono text-xl tracking-[0.1em] text-white/90">
              {BRAND_NAME}<span className="text-white/30">.{BRAND_LAST}</span>
            </span>
          </a>

          <nav className="hidden md:flex items-center gap-9">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="font-mono text-lg tracking-wide text-white/65 hover:text-white transition-colors duration-200">
                {link.label}
              </a>
            ))}
            <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="font-mono text-lg tracking-wide rounded-full px-5 py-2.5 bg-teal-400 text-[#0A0E14] font-medium hover:bg-teal-300 hover:-translate-y-0.5 transition-all duration-200">
              Let&apos;s Talk
            </a>
          </nav>

          <button className="md:hidden text-white/80" onClick={() => setMenuOpen((v) => !v)} aria-label="Toggle menu">
            {menuOpen ? <X className="w-7 h-7" /> : <Menu className="w-7 h-7" />}
          </button>
        </div>

        {menuOpen && (
          <div className="md:hidden bg-[#0A0E14] border-b border-white/[0.06] px-6 pb-6 pt-2 flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} onClick={closeMenu} className="font-mono text-xl text-white/60 hover:text-white py-3.5 border-b border-white/[0.04]">
                {link.label}
              </a>
            ))}
            <a href={CALENDLY_URL} target="_blank" rel="noreferrer" onClick={closeMenu} className="font-mono text-xl text-teal-300 py-3.5">
              Let&apos;s Talk →
            </a>
          </div>
        )}
      </header>

      {/* ================= HERO ================= */}
      <section id="top" className="relative pt-40 pb-20 md:pt-52 md:pb-24 px-6 md:px-8 overflow-hidden dot-grid">
        <div
          className="pointer-events-none absolute -top-40 right-[-10%] w-[620px] h-[620px] rounded-full opacity-[0.12] blur-3xl"
          style={{ background: "radial-gradient(circle, #2CB1A3 0%, transparent 70%)", animation: "float 11s ease-in-out infinite" }}
        />
        <div
          className="pointer-events-none absolute top-[20%] left-[-15%] w-[420px] h-[420px] rounded-full opacity-[0.08] blur-3xl"
          style={{ background: "radial-gradient(circle, #3B82F6 0%, transparent 70%)" }}
        />

        <div className="max-w-6xl mx-auto relative grid lg:grid-cols-[1.1fr_0.95fr] gap-16 items-center">
          <div>
            <Reveal>
              <div className="inline-flex items-center gap-2 font-mono text-lg tracking-[0.12em] text-teal-300/90 rounded-full border border-teal-400/25 bg-teal-400/5 px-4 py-2 mb-8">
                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                5+ YEARS OF GOHIGHLEVEL EXPERIENCE
              </div>
            </Reveal>

            <Reveal delay={80}>
              <h1 className="font-[Space_Grotesk,sans-serif] text-[2.6rem] leading-[1.06] sm:text-5xl md:text-6xl font-medium tracking-tight text-white">
                Websites and Automated Systems
                <span className="block grad-text">That Turn Leads Into Customers</span>
              </h1>
            </Reveal>

            <Reveal delay={160}>
              <p className="mt-8 text-xl md:text-2xl text-white/60 max-w-xl leading-relaxed">
                I design GoHighLevel websites, funnels, CRM systems, and automations for service businesses — so more enquiries are captured, followed up, and moved toward a booked appointment.
              </p>
            </Reveal>

            <Reveal delay={240}>
              <div className="mt-10 flex flex-col sm:flex-row gap-4">
                <a
                  href="#work"
                  className="group inline-flex items-center justify-center gap-2 rounded-full bg-teal-400 text-[#0A0E14] text-2xl font-medium px-8 py-4 hover:bg-teal-300 hover:-translate-y-0.5 transition-all duration-200 shadow-[0_8px_30px_-8px_rgba(45,217,197,0.5)]"
                >
                  View My Work <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </a>
                <a
                  href={CALENDLY_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-white/15 text-white/85 text-2xl font-medium px-8 py-4 hover:border-teal-400/50 hover:bg-white/[0.03] hover:-translate-y-0.5 transition-all duration-200"
                >
                  Let&apos;s Talk
                </a>
              </div>
              <p className="mt-4 text-base text-white/40 font-mono">Prefer a quick answer? Tell me where leads are getting stuck and I&apos;ll reply within 5 minutes.</p>
            </Reveal>
          </div>

          <Reveal delay={200}>
            <HeroVisual />
          </Reveal>
        </div>
      </section>

      {/* ================= EARLY SOCIAL PROOF ================= */}
      <VideoTestimonialCard />

      {/* ================= INDUSTRIES MARQUEE ================= */}
      <IndustriesMarquee />

      {/* ================= ABOUT ================= */}
      <section id="about" className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06]">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-[0.85fr_1.15fr] gap-14 items-start">
          <Reveal>
            <div className="relative aspect-[4/5] rounded-2xl border border-white/[0.08] overflow-hidden">
              <SmartImage src={PORTRAIT_IMAGE} alt="Ayomide Ariyo" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0A0E14]/60 via-transparent to-transparent" />
              <div className="absolute bottom-5 left-5 right-5 rounded-xl border border-teal-400/25 bg-[#0B121B]/90 backdrop-blur-sm px-4 py-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
                <span className="font-mono text-base text-white/70">Available for new projects</span>
              </div>
            </div>
          </Reveal>

          <div>
            <Reveal>
              <Eyebrow index="01">About</Eyebrow>
              <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl leading-[1.1] font-medium text-white mb-6">
                Building More Than Just Websites
              </h2>
              <p className="text-white/60 text-3xl leading-relaxed max-w-xl">
                I build complete digital systems — connecting the website to lead capture, the CRM, follow-up, appointment booking, and the sales handoff.
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-6 font-mono text-lg text-teal-300/90">
                <span className="rounded-full border border-teal-400/25 bg-teal-400/[0.06] px-3 py-1.5">Website</span>
                <ArrowRight className="w-4 h-4 text-teal-400/40" />
                <span className="rounded-full border border-teal-400/25 bg-teal-400/[0.06] px-3 py-1.5">Lead Capture</span>
                <ArrowRight className="w-4 h-4 text-teal-400/40" />
                <span className="rounded-full border border-teal-400/25 bg-teal-400/[0.06] px-3 py-1.5">CRM</span>
                <ArrowRight className="w-4 h-4 text-teal-400/40" />
                <span className="rounded-full border border-teal-400/25 bg-teal-400/[0.06] px-3 py-1.5">Follow-Up</span>
                <ArrowRight className="w-4 h-4 text-teal-400/40" />
                <span className="rounded-full border border-teal-400/25 bg-teal-400/[0.06] px-3 py-1.5">Appointment</span>
                <ArrowRight className="w-4 h-4 text-teal-400/40" />
                <span className="rounded-full border border-teal-400/25 bg-teal-400/[0.06] px-3 py-1.5">Sales</span>
              </div>
            </Reveal>

            <div className="grid sm:grid-cols-2 gap-4 mt-10">
              {CAPABILITIES.map((cap, i) => (
                <CapabilityCard key={cap.title} cap={cap} delay={i * 80} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ================= FEATURED WORK ================= */}
      <section id="work" className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06] bg-[#0B111A]">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <Eyebrow index="02">Selected Work</Eyebrow>
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-14">
              <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white">Selected Work</h2>
              <p className="text-white/65 text-2xl max-w-sm">A few of the websites and systems I&apos;ve built recently. Replace the placeholders with real screenshots, outcomes, and live links before launch.</p>
            </div>
          </Reveal>

          <FeaturedWork onOpenModal={setModalProject} />
        </div>
      </section>

      {/* ================= SYSTEM FLOW ================= */}
      <section id="systems" className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06]">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <Eyebrow index="03">Systems</Eyebrow>
            <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl leading-[1.1] font-medium text-white max-w-2xl">
              I Don&apos;t Just Build Websites. <span className="grad-text">I Build Systems.</span>
            </h2>
            <p className="mt-6 text-white/60 text-3xl leading-relaxed max-w-2xl">
              Every project connects the same seven stages — so a lead doesn&apos;t just land on a page, they move all the way through to a booked appointment.
            </p>
          </Reveal>

          <SystemFlow />
        </div>
      </section>

      {/* ================= SERVICES ================= */}
      <section id="services" className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06] bg-[#0B111A]">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <Eyebrow index="04">What I Do</Eyebrow>
            <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white mb-16">What I Do</h2>
          </Reveal>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {SERVICES.map((service, i) => (
              <ServiceCard key={service.title} service={service} delay={i * 60} />
            ))}
          </div>
        </div>
      </section>

      {/* ================= TECH STACK ================= */}
      <section className="px-6 md:px-8 py-24 md:py-28 border-b border-white/[0.06]">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <Eyebrow index="05">Toolkit</Eyebrow>
            <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white mb-12">
              A Connected Technology Ecosystem
            </h2>
          </Reveal>
          <Reveal delay={100}>
            <div className="flex flex-wrap gap-3.5 justify-center">
              {TECH_STACK.map((tech, i) => (
                <span
                  key={tech}
                  className="flex items-center gap-2 font-mono text-lg text-white/70 rounded-full border border-white/[0.1] hover:border-teal-400/50 hover:text-teal-300 hover:bg-teal-400/[0.06] transition-all duration-300 px-5 py-3 cursor-default"
                  style={{ animation: `float ${5 + (i % 4)}s ease-in-out infinite`, animationDelay: `${i * 0.2}s` }}
                >
                  <Code2 className="w-3.5 h-3.5 text-teal-400/70" />
                  {tech}
                </span>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ================= STATS ================= */}
      <section id="experience" className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06] bg-[#0B111A]">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <Eyebrow index="06">Experience</Eyebrow>
            <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white mb-14">By the Numbers</h2>
          </Reveal>

          <div className="grid sm:grid-cols-3 gap-5 mb-14">
            {STATS.map((stat, i) => (
              <StatBlock key={stat.label} stat={stat} delay={i * 100} />
            ))}
          </div>

          <Reveal delay={150}>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {["Websites & Funnels", "CRM Systems", "Workflow Automation", "Lead Management", "Integrations", "AI Automation"].map((tag) => (
                <div key={tag} className="rounded-xl border border-white/[0.08] bg-[#0B111A] px-7 py-6 flex items-center gap-3 hover:border-white/[0.16] hover:bg-[#0F1B24] transition-colors duration-300">
                  <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                  <span className="text-white/75 text-xl">{tag}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ================= TESTIMONIALS ================= */}
      {TESTIMONIALS.length > 0 && (
        <section id="reviews" className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06]">
          <div className="max-w-6xl mx-auto">
            <Reveal>
              <div className="text-center mb-16">
                <div className="inline-flex">
                  <Eyebrow index="07">Reviews</Eyebrow>
                </div>
                <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white">
                  Trusted by Clients I&apos;ve Worked With
                </h2>
              </div>
            </Reveal>
            <Reveal delay={100}>
              <TestimonialCarousel />
            </Reveal>
          </div>
        </section>
      )}

      {/* ================= HOW I WORK ================= */}
      <section className="px-6 md:px-8 py-24 md:py-32 border-b border-white/[0.06] bg-[#0B111A]">
        <div className="max-w-4xl mx-auto">
          <Reveal>
            <Eyebrow index="08">How I Work</Eyebrow>
            <h2 className="font-[Space_Grotesk,sans-serif] text-3xl md:text-4xl font-medium text-white mb-16">A Clear, Repeatable Process</h2>
          </Reveal>

          <div className="relative">
            <div className="absolute left-6 top-2 bottom-2 w-px bg-gradient-to-b from-teal-400/50 via-white/10 to-transparent hidden sm:block" />
            <div className="space-y-10">
              {PROCESS_STEPS.map((step, i) => (
                <Reveal key={step.num} delay={i * 100}>
                  <div className="flex gap-6 sm:gap-8">
                    <div className="relative shrink-0 w-12 h-12 rounded-full border border-teal-400/30 bg-[#0B111A] flex items-center justify-center font-mono text-lg text-teal-300 z-10">
                      {step.num}
                    </div>
                    <div className="pt-1.5">
                      <h3 className="font-[Space_Grotesk,sans-serif] text-3xl text-white font-medium mb-2">{step.title}</h3>
                      <p className="text-white/65 text-2xl leading-relaxed max-w-xl">{step.desc}</p>
                    </div>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section
        id="contact"
        onMouseMove={handleCtaMouseMove}
        className="relative px-6 md:px-8 py-28 md:py-40 border-b border-white/[0.06] overflow-hidden dot-grid"
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-30 transition-[background] duration-300"
          style={{
            background: `radial-gradient(500px circle at ${ctaGlow.x}% ${ctaGlow.y}%, rgba(45,217,197,0.25), transparent 60%)`,
          }}
        />
        <div
          className="pointer-events-none absolute bottom-[-30%] left-[-10%] w-[560px] h-[560px] rounded-full opacity-[0.14] blur-3xl"
          style={{ background: "radial-gradient(circle, #2CB1A3 0%, transparent 70%)", animation: "float 10s ease-in-out infinite" }}
        />

        <FloatingBadge icon={Zap} label="Automation Active" className="hidden lg:flex top-10 left-[8%] opacity-60" delay="0.5s" duration="8s" />
        <FloatingBadge icon={CheckCircle2} label="System Connected" className="hidden lg:flex bottom-14 right-[10%] opacity-60" delay="1.5s" duration="9s" />

        <div className="max-w-3xl mx-auto text-center relative">
          <Reveal>
            <h2 className="font-[Space_Grotesk,sans-serif] text-4xl md:text-6xl leading-[1.1] font-medium text-white">
              Ready for a Website or CRM
              <br />
              System That Works?
            </h2>
            <p className="mt-7 text-white/60 text-3xl">
              Tell me what you want to improve. I&apos;ll help map the right website, CRM, and automation path for your business.
            </p>
            <div className="mt-10 flex flex-wrap flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href={CALENDLY_URL}
                target="_blank"
                rel="noreferrer"
                className="group inline-flex items-center gap-2 rounded-full bg-teal-400 text-[#0A0E14] text-2xl font-medium px-9 py-4.5 hover:bg-teal-300 hover:-translate-y-0.5 transition-all duration-200 shadow-[0_8px_30px_-8px_rgba(45,217,197,0.5)]"
              >
                Book a Call <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </a>
              <a
                href={WHATSAPP_URL}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 text-white/85 text-2xl font-medium px-9 py-4.5 hover:border-teal-400/50 hover:bg-white/[0.03] hover:-translate-y-0.5 transition-all duration-200"
              >
                <MessageCircle className="w-5 h-5" /> WhatsApp
              </a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="px-6 md:px-8 py-16">
        <div className="max-w-6xl mx-auto grid sm:grid-cols-3 gap-10 pb-12 border-b border-white/[0.06]">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <LogoMark className="w-20 h-20" />
              <span className="font-mono text-xl tracking-[0.1em] text-white/90">{BRAND_NAME} {BRAND_LAST}</span>
            </div>
            <p className="text-xl text-white/65">Websites, CRM systems, and follow-up automation for service businesses.</p>
            {/* <p className="mt-3 text-base text-white/40">Projects typically begin with a short discovery conversation. Replace this line with your response time, service area, or starting project range.</p> */}
          </div>

          <div>
            <span className="font-mono text-base tracking-widest text-white/35 uppercase">Quick Links</span>
            <div className="mt-4 flex flex-col gap-2.5">
              {FOOTER_LINKS.map((link) => (
                <a key={link.href} href={link.href} className="text-white/65 hover:text-teal-300 transition-colors text-xl w-fit">
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          <div>
            <span className="font-mono text-base tracking-widest text-white/35 uppercase">Connect</span>
            <div className="mt-4 flex flex-col gap-2.5">
              <a href={WHATSAPP_URL} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xl text-white/65 hover:text-teal-300 transition-colors w-fit">
                <MessageCircle className="w-4 h-4" /> WhatsApp
              </a>
              <a href={`mailto:${CONTACT.email}`} className="flex items-center gap-2 text-xl text-white/65 hover:text-teal-300 transition-colors w-fit">
                <Mail className="w-4 h-4" /> Email
              </a>
              <a href={CONTACT.linkedin} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xl text-white/65 hover:text-teal-300 transition-colors w-fit">
                <LinkIcon className="w-4 h-4" /> LinkedIn
              </a>
              <a href={CONTACT.upwork} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xl text-white/65 hover:text-teal-300 transition-colors w-fit">
                <Briefcase className="w-4 h-4" /> Upwork
              </a>
            </div>
          </div>
        </div>
        <div className="max-w-6xl mx-auto mt-8">
          <p className="font-mono text-base text-white/25">
            © {new Date().getFullYear()} Ayomide Ariyo. Built with GoHighLevel &amp; automation in mind.
          </p>
        </div>
      </footer>
    </div>
  );
}
