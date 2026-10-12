import React from 'react';
import { NodeProps } from '@xyflow/react';

interface PhaseGroupData {
  phaseNumber: number;
  phaseTitle: string;
  phaseSubtitle: string;
  width: number;
  height: number;
}

export const PhaseGroupNode: React.FC<NodeProps> = ({ data }) => {
  const d = data as unknown as PhaseGroupData;

  return (
    <div
      style={{ width: d.width, height: d.height }}
      className="rounded-2xl bg-slate-900/35 border border-slate-800/70 p-3.5 flex flex-col justify-between pointer-events-none transition-all shadow-inner shadow-black/40"
    >
      {/* Swimlane Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sap-blue shadow-sm shadow-sap-blue/60"></span>
          <span className="text-[11px] font-mono font-bold tracking-wider text-slate-200 uppercase">
            {d.phaseTitle}
          </span>
        </div>
        <span className="text-[9px] font-mono font-semibold text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/60">
          P{d.phaseNumber}
        </span>
      </div>

      {/* Swimlane Footer Subtitle */}
      <div className="pt-2 border-t border-slate-800/40 text-[9px] font-mono text-slate-400 truncate">
        {d.phaseSubtitle}
      </div>
    </div>
  );
};
