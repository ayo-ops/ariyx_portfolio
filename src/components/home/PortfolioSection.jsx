import React, { useState } from "react";
import SectionHeader from "../common/SectionHeader";
import ScrollReveal from "../common/ScrollReveal";
import { PROJECTS, PROJECT_CATEGORIES } from "../../data/projects";
import ProjectModal from "./ProjectModal";
import { ExternalLink, Layers, ArrowUpRight } from "lucide-react";
import Button from "../common/Button";

export default function PortfolioSection() {
  const [activeCategory, setActiveCategory] = useState("All Systems");
  const [selectedProject, setSelectedProject] = useState(null);

  const filteredProjects =
    activeCategory === "All Systems"
      ? PROJECTS
      : PROJECTS.filter((p) => p.category === activeCategory);

  return (
    <>
      <section id="portfolio" className="py-24 sm:py-32 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-12">
            <ScrollReveal delay={0}>
              <SectionHeader
                badge="Verified Work"
                badgeVariant="electric"
                title="Selected Client Systems &"
                highlightText="Implementations."
                highlightColor="electric"
                description="A curated selection of real web environments, automated lead funnels, and CRM portals built for high-performance service and SaaS businesses."
                className="mb-0"
              />
            </ScrollReveal>

            {/* Category Filter Pills */}
            <ScrollReveal delay={100}>
              <div className="flex flex-wrap gap-2 shrink-0">
                {PROJECT_CATEGORIES.map((category) => (
                  <button
                    key={category}
                    onClick={() => setActiveCategory(category)}
                    className={`px-4 py-2 rounded-full font-mono text-xs sm:text-[13px] font-medium transition-all border cursor-pointer ${
                      activeCategory === category
                        ? "bg-electric text-white border-electric shadow-sm"
                        : "bg-midnight/70 text-soft-muted border-deep-blue hover:border-white/20 hover:text-white"
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </ScrollReveal>
          </div>

          {/* Project Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {filteredProjects.map((project, idx) => (
              <ScrollReveal key={project.id} delay={idx * 60}>
                <div
                  className="group h-full rounded-2xl border border-deep-blue bg-midnight/85 overflow-hidden flex flex-col justify-between hover:border-electric/70 transition-all duration-300 shadow-card hover:shadow-card-hover hover:-translate-y-1.5"
                >
                  <div>
                    {/* Mockup Image Preview with Gentle Zoom */}
                    <div
                      onClick={() => setSelectedProject(project)}
                      className="relative aspect-[16/10] overflow-hidden bg-midnight-dark border-b border-deep-blue cursor-pointer"
                    >
                      <img
                        src={project.image}
                        alt={`${project.name} preview`}
                        className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-midnight/20 group-hover:bg-midnight/5 transition-colors" />
                      
                      {/* Industry Tag Overlay */}
                      <div className="absolute top-3 left-3 px-3 py-1 rounded-md bg-midnight/90 backdrop-blur-sm border border-white/10 text-xs font-mono text-soft-white font-medium">
                        {project.industry}
                      </div>
                    </div>

                    {/* Card Content */}
                    <div className="p-6 sm:p-7">
                      <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight group-hover:text-electric-light transition-colors leading-snug">
                        {project.name}
                      </h3>
                      
                      {/* 14.5px - 15.5px readable text */}
                      <p className="mt-3 text-[14.5px] sm:text-[15px] text-soft-muted leading-relaxed font-normal line-clamp-3">
                        {project.description}
                      </p>

                      {/* Services Tags */}
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

                  {/* Card Actions Footer */}
                  <div className="px-6 py-4 border-t border-deep-blue/70 bg-midnight-dark/50 flex items-center justify-between">
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

        </div>
      </section>

      {/* Project Detail Modal */}
      <ProjectModal
        project={selectedProject}
        onClose={() => setSelectedProject(null)}
      />
    </>
  );
}
