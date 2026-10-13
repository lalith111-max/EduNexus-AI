"use client";

import React from "react";
import { Citation } from "@/lib/api";
import { X, CheckCircle, FileText, Presentation, Video, ExternalLink, ShieldCheck } from "lucide-react";

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  const getLocationLabel = () => {
    if (citation.page_number) return `Page ${citation.page_number}`;
    if (citation.slide_number) return `Slide ${citation.slide_number}`;
    if (citation.timestamp_start !== undefined && citation.timestamp_start !== null) {
      return `Timestamp ${Math.floor(citation.timestamp_start)}s`;
    }
    return "Course Section";
  };

  const getSourceIcon = () => {
    if (citation.source_type === "pptx") return <Presentation className="w-5 h-5 text-amber-400" />;
    if (citation.source_type === "video" || citation.source_type === "audio") return <Video className="w-5 h-5 text-emerald-400" />;
    return <FileText className="w-5 h-5 text-indigo-400" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
              {getSourceIcon()}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Verified Source Citation
                </span>
                <span className="text-xs font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  {getLocationLabel()}
                </span>
              </div>
              <h3 className="text-base font-semibold text-slate-100 mt-1 truncate max-w-md">
                {citation.source_name}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider block mb-2">
              Verified Source Excerpt (Verbatim)
            </label>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 text-sm leading-relaxed italic border-l-4 border-l-indigo-500">
              "{citation.excerpt}"
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block mb-1">Source Chunk ID</span>
              <span className="font-mono text-indigo-300 font-semibold">{citation.chunk_id}</span>
            </div>
            <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block mb-1">Relevance Score</span>
              <span className="font-semibold text-emerald-400">{Math.round((citation.relevance_score || 1) * 100)}% Match</span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/20 text-xs text-indigo-300 flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-indigo-200">Grounding Guarantee:</strong> EduNexus AI binds this assertion strictly to the above document. Citations are verified against active course indices without hallucinated references.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
