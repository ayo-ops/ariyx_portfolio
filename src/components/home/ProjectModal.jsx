import React, { useEffect } from "react";
import { X, ExternalLink, Globe, Layers, ArrowUpRight } from "lucide-react";
import Button from "../common/Button";

export default function ProjectModal({ project, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    if (project) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [project, onClose]);

  if (!project) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-midnight-dark/85 backdrop-blur-md"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl bg-midnight rounded-2xl border border-deep-blue shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-deep-blue bg-midnight-dark/90">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-deep-blue/60 text-teal uppercase">
              {project.industry}
            </span>
            <span className="text-soft-dim font-mono text-xs">
              // Case Study #{String(project.id).padStart(2, "0")}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-soft-dim hover:text-white hover:bg-deep-blue transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content Scrollable Area */}
        <div className="overflow-y-auto p-6 sm:p-8 space-y-6">
          {/* Project Mockup Visual */}
          <div className="relative aspect-video rounded-xl overflow-hidden border border-deep-blue bg-midnight-dark">
            <img
              src={project.image}
              alt={`${project.name} Implementation Mockup`}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Project Details */}
          <div>
            <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              {project.name}
            </h3>
            <p className="mt-3 text-base text-soft-muted leading-relaxed">
              {project.description}
            </p>
          </div>

          {/* Services Deployed */}
          <div>
            <h4 className="font-mono text-xs uppercase tracking-wider text-soft-dim mb-3">
              Configured Capabilities
            </h4>
            <div className="flex flex-wrap gap-2">
              {project.services.map((service, i) => (
                <span
                  key={i}
                  className="font-mono text-xs px-3 py-1.5 rounded-lg bg-deep-blue/40 border border-deep-blue text-soft-white"
                >
                  {service}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="p-6 border-t border-deep-blue bg-midnight-dark/80 flex items-center justify-between gap-4">
          <button
            onClick={onClose}
            className="text-xs font-mono text-soft-dim hover:text-soft-white transition-colors"
          >
            Close Overview
          </button>

          {project.url && (
            <Button
              href={project.url}
              target="_blank"
              variant="primary"
              size="sm"
              icon={ExternalLink}
            >
              Open Live Environment
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
