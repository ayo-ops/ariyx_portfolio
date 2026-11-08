import React, { useState } from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import SectionHeader from "../components/common/SectionHeader";
import ScrollReveal from "../components/common/ScrollReveal";
import Badge from "../components/common/Badge";
import Button from "../components/common/Button";
import ProjectModal from "../components/home/ProjectModal";
import VideoModal from "../components/home/VideoModal";
import { PROJECTS, PROJECT_CATEGORIES } from "../data/projects";
import { VIDEO_TESTIMONIAL } from "../data/testimonials";
import { CONTACT } from "../data/navigation";
import {
  ExternalLink,
  Layers,
  Calendar,
  Play,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";

export default function PortfolioPage() {
  const [activeCategory, setActiveCategory] = useState("All Systems");
  const [selectedProject, setSelectedProject] = useState(null);
  const [isVideoOpen, setIsVideoOpen] = useState(false);

  const filteredProjects =
    activeCategory === "All Systems"
      ? PROJECTS
      : PROJECTS.filter((p) => p.category === activeCategory);

  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />

      <main className="pt-28 sm:pt-36 pb-24">
        {/* Header Section */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16 text-center">
          <ScrollReveal delay={0}>
            <div className="inline-flex mb-4">
              <Badge variant="electric" icon={Layers} size="md">
                Verified Work
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
              Real Client Environments &amp;{" "}
              <span className="text-electric-light">Production Systems.</span>
            </h1>
            <p className="mt-6 text-[16.5px] sm:text-[18px] text-soft-muted max-w-3xl mx-auto leading-relaxed font-normal">
              A comprehensive showcase of conversion-optimized web platforms, multi-location SaaS architectures, and automated CRM pipelines delivered for high-performance businesses.
            </p>
          </ScrollReveal>
        </section>

        {/* Filter Pills */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-12">
          <ScrollReveal delay={80}>
            <div className="flex flex-wrap items-center justify-center gap-2.5">
              {PROJECT_CATEGORIES.map((category) => (
                <button
                  key={category}
                  onClick={() => setActiveCategory(category)}
                  className={`px-5 py-2.5 rounded-full font-mono text-xs sm:text-[13px] font-semibold transition-all border cursor-pointer ${
                    activeCategory === category
                      ? "bg-electric text-white border-electric shadow-sm"
                      : "bg-midnight-dark text-soft-muted border-deep-blue hover:border-white/20 hover:text-white"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </ScrollReveal>
        </section>

        {/* Projects Grid */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-28">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredProjects.map((project, idx) => (
              <ScrollReveal key={project.id} delay={idx * 50}>
                <div className="group h-full rounded-2xl border border-deep-blue bg-midnight-dark overflow-hidden flex flex-col justify-between hover:border-electric/70 transition-all duration-300 shadow-card hover:shadow-card-hover hover:-translate-y-1.5">
                  <div>
                    {/* Mockup Image Preview */}
                    <div
                      onClick={() => setSelectedProject(project)}
                      className="relative aspect-[16/10] overflow-hidden bg-midnight border-b border-deep-blue cursor-pointer"
                    >
                      <img
                        src={project.image}
                        alt={`${project.name} Implementation Mockup`}
                        className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-midnight/20 group-hover:bg-midnight/5 transition-colors" />
                      
                      <div className="absolute top-3 left-3 px-3 py-1 rounded-md bg-midnight/90 backdrop-blur-sm border border-white/10 text-xs font-mono text-soft-white font-medium">
                        {project.industry}
                      </div>
                    </div>

                    {/* Card Content */}
                    <div className="p-6 sm:p-7">
                      <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight group-hover:text-electric-light transition-colors leading-snug">
                        {project.name}
                      </h3>
                      
                      <p className="mt-3 text-[14.5px] sm:text-[15px] text-soft-muted leading-relaxed font-normal">
                        {project.description}
                      </p>

                      <div className="mt-4 flex flex-wrap gap-1.5">
                        {project.services.map((service, i) => (
                          <span
                            key={i}
                            className="font-mono text-xs px-2.5 py-1 rounded-md bg-deep-blue/40 border border-deep-blue/80 text-soft-white/90 font-medium"
                          >
                            {service}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div className="px-6 py-4 border-t border-deep-blue/70 bg-midnight/60 flex items-center justify-between">
                    <button
                      onClick={() => setSelectedProject(project)}
                      className="text-xs font-mono font-semibold text-soft-dim hover:text-white transition-colors cursor-pointer"
                    >
                      System Details
                    </button>

                    {project.url && (
                      <a
                        href={project.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-teal hover:text-teal-light transition-colors"
                      >
                        <span>Live Site</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </section>

        {/* Video Testimonial Feature Card */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16">
          <ScrollReveal delay={0}>
            <div className="rounded-3xl border border-deep-blue bg-midnight-dark/95 p-8 sm:p-12 shadow-2xl">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                <div className="lg:col-span-5">
                  <div
                    onClick={() => setIsVideoOpen(true)}
                    className="group relative aspect-video rounded-xl overflow-hidden border border-deep-blue bg-midnight cursor-pointer hover:border-teal/60 transition-all duration-300"
                  >
                    <img
                      src={VIDEO_TESTIMONIAL.poster}
                      alt={`${VIDEO_TESTIMONIAL.client} Video Review`}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-midnight/25 flex items-center justify-center">
                      <div className="w-14 h-14 rounded-full bg-teal text-midnight-dark flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                        <Play className="w-6 h-6 ml-1 fill-current" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-7 space-y-4">
                  <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-teal font-semibold">
                    <ShieldCheck className="w-4 h-4" /> Live Case Interview
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
                    Hear How Patty Jackson Connected Her Entire Lead &amp; Certification Funnel.
                  </h3>
                  <p className="text-[15px] sm:text-[16px] text-soft-muted leading-relaxed font-normal">
                    {VIDEO_TESTIMONIAL.caption}
                  </p>
                  <div className="pt-2 flex items-center gap-4">
                    <button
                      onClick={() => setIsVideoOpen(true)}
                      className="inline-flex items-center gap-2 text-sm font-bold text-teal hover:text-teal-light font-mono transition-colors cursor-pointer"
                    >
                      Watch 2-Minute Interview <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </ScrollReveal>
        </section>
      </main>

      <ProjectModal
        project={selectedProject}
        onClose={() => setSelectedProject(null)}
      />

      <VideoModal
        isOpen={isVideoOpen}
        onClose={() => setIsVideoOpen(false)}
        videoSrc={VIDEO_TESTIMONIAL.src}
        poster={VIDEO_TESTIMONIAL.poster}
        title={`${VIDEO_TESTIMONIAL.client} (${VIDEO_TESTIMONIAL.business})`}
      />

      <Footer />
    </div>
  );
}
