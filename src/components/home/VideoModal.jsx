import React, { useEffect } from "react";
import { X } from "lucide-react";

export default function VideoModal({ isOpen, onClose, videoSrc, poster, title }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-midnight-dark/85 backdrop-blur-md"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl bg-midnight rounded-2xl border border-deep-blue shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-deep-blue bg-midnight-dark/80">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal" />
            <span className="font-mono text-xs uppercase tracking-wider text-soft-dim">
              Verified Client Testimonial · {title}
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

        {/* Video Player */}
        <div className="relative aspect-video bg-black">
          <video
            src={videoSrc}
            poster={poster}
            controls
            autoPlay
            playsInline
            className="w-full h-full object-contain"
          >
            Your browser does not support the video tag.
          </video>
        </div>
      </div>
    </div>
  );
}
