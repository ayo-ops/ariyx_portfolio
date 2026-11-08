export const CONTACT = {
  email: "ariyoleke232@gmail.com",
  whatsappNumber: "2349152581764",
  whatsappUrl: "https://wa.me/2349152581764",
  calendlyUrl: "https://calendly.com/ariyoleke232/30min",
  linkedin: "https://www.linkedin.com/in/ariyo-emmanuel/",
  upwork: "https://www.upwork.com/freelancers/~01ca944a52609188c9?mp_source=share",
};

export const NAV_LINKS = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Services", href: "/services" },
  { label: "Solutions", href: "/solutions" },
  { label: "Portfolio", href: "/portfolio" },
  { label: "Insights", href: "/insights" },
  { label: "Contact", href: "/contact" },
];

export const FOOTER_LINKS = {
  services: [
    { label: "CRM Implementation", href: "/services#crm-implementation" },
    { label: "GoHighLevel Setup", href: "/services#gohighlevel-setup" },
    { label: "Sales & Lead Systems", href: "/services#sales-lead-management" },
    { label: "Process Automation", href: "/services#process-automation" },
    { label: "AI Agents & Voice AI", href: "/services#ai-agents-voice" },
    { label: "API & Webhook Integrations", href: "/services#api-webhook-integrations" },
  ],
  solutions: [
    { label: "Missed Leads Solution", href: "/solutions#missed-leads" },
    { label: "Pipeline Leakage Fix", href: "/solutions#poor-follow-up" },
    { label: "No-Show Reduction", href: "/solutions#high-no-shows" },
    { label: "Manual Process Automation", href: "/solutions#manual-processes" },
    { label: "Data Silo Integration", href: "/solutions#disconnected-tools" },
  ],
  company: [
    { label: "About Ariyx Systems", href: "/about" },
    { label: "Verified Portfolio", href: "/portfolio" },
    { label: "Architecture Insights", href: "/insights" },
    { label: "Contact & Scoping", href: "/contact" },
    { label: "Schedule Consultation", href: CONTACT.calendlyUrl, external: true },
  ],
};
