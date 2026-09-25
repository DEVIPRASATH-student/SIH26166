import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Network, RefreshCw, AlertTriangle, XCircle } from 'lucide-react';
import { api } from '../services/api';

export const EntityGraph: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getFullGraph();
      
      const styledNodes: Node[] = (data?.nodes || []).map((n: any) => {
        let bgColor = '#ffffff';
        let borderColor = '#cbd5e1';
        let textColor = '#0f172a';

        const typeStr = String(n.type).toUpperCase();

        if (typeStr.includes('ENTITY')) {
          bgColor = '#e0e7ff';
          borderColor = '#6366f1';
          textColor = '#1e1b4b';
        } else if (typeStr.includes('OBSERVATION')) {
          bgColor = '#e0f2fe';
          borderColor = '#0284c7';
          textColor = '#075985';
        } else if (typeStr.includes('EVIDENCE')) {
          bgColor = '#d1fae5';
          borderColor = '#059669';
          textColor = '#064e3b';
        } else if (typeStr.includes('HYPOTHESIS')) {
          bgColor = '#f1f5f9';
          borderColor = '#64748b';
          textColor = '#0f172a';
        } else if (typeStr.includes('GAP')) {
          bgColor = '#fef3c7';
          borderColor = '#d97706';
          textColor = '#78350f';
        } else if (typeStr.includes('RECOMMENDATION')) {
          bgColor = '#d1fae5';
          borderColor = '#10b981';
          textColor = '#064e3b';
        }

        return {
          id: n.id,
          type: 'default',
          position: n.position || { x: Math.random() * 400, y: Math.random() * 400 },
          data: {
            label: (
              <div className="p-1 font-sans text-left">
                <div className="text-[9px] uppercase tracking-wider text-slate-700 font-black">
                  {n.type}
                </div>
                <div className="text-xs font-black truncate max-w-[160px] text-[#0d2247]">{n.data?.label || n.id}</div>
                {n.data?.confidence !== undefined && (
                  <div className="text-[10px] text-emerald-800 font-extrabold mt-0.5">
                    Conf: {Math.round(n.data.confidence * 100)}%
                  </div>
                )}
              </div>
            ),
            raw: n.data || n,
            nodeType: n.type,
          },
          style: {
            background: bgColor,
            color: textColor,
            border: `2px solid ${borderColor}`,
            borderRadius: '12px',
            width: 190,
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          },
        };
      });

      const styledEdges: Edge[] = (data?.edges || []).map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: e.animated,
        style: e.style || { stroke: '#0284c7', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 12,
          height: 12,
          color: e.style?.stroke || '#0284c7',
        },
        labelStyle: { fill: '#334155', fontSize: 10, fontFamily: 'sans-serif', fontWeight: 800 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.95 },
      }));

      setNodes(styledNodes);
      setEdges(styledEdges);
    } catch (err: any) {
      console.error('Failed to load graph', err);
      setError(err?.message || 'Graph service unavailable.');
    } finally {
      setIsLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNodeData(node.data);
  };

  return (
    <div className="space-y-4 font-sans">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-black px-2.5 py-0.5 rounded bg-indigo-100 text-indigo-950 border border-indigo-300">
              WORLD MODEL MEMORY LAYER
            </span>
            <span className="text-xs text-slate-800 font-extrabold">Ontological Relational Graph</span>
          </div>
          <h1 className="text-xl font-black text-[#0d2247] mt-1.5 flex items-center space-x-2">
            <Network className="w-6 h-6 text-blue-700" />
            <span>Lunar Entity Knowledge Graph & Relational World Model</span>
          </h1>
          <p className="text-xs text-slate-900 font-bold mt-1">
            NetworkX relational ontology linking persistent lunar entities, multi-modal observation streams, physics evidence, and hypotheses.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchGraph}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-extrabold transition-all shadow-sm active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Graph</span>
          </button>
        </div>
      </div>

      {/* Mandatory Relational Guardrails Notice */}
      <div className="p-5 rounded-2xl border border-amber-300 bg-amber-50/80 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-bold shadow-sm">
        <div className="flex items-start space-x-2.5">
          <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-black text-amber-950 block text-xs">
              GUARDRAIL 1: ENTITY ASSOCIATION ≠ DIRECT IMAGE CORRESPONDENCE
            </span>
            <p className="text-slate-900 mt-1 text-[11px] leading-relaxed font-bold">
              Two observations can both associate with the same persistent physical crater without requiring direct pixel-to-pixel image registration.
            </p>
          </div>
        </div>

        <div className="flex items-start space-x-2.5">
          <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-black text-amber-950 block text-xs">
              GUARDRAIL 2: SPATIAL PROXIMITY ≠ ENTITY IDENTITY
            </span>
            <p className="text-slate-900 mt-1 text-[11px] leading-relaxed font-bold">
              Distinct lunar features occurring near each other in geodetic coordinates maintain discrete physical identities rather than being merged blindly.
            </p>
          </div>
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-800 font-bold bg-white rounded-2xl border border-slate-200 shadow-sm flex items-center justify-center space-x-2">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-700" />
          <span>Rendering World Model ontology nodes and edges...</span>
        </div>
      )}

      {error && !isLoading && (
        <div className="p-5 rounded-2xl bg-rose-50 border border-rose-300 text-xs text-rose-950 font-bold flex items-center space-x-3 shadow-sm">
          <XCircle className="w-5 h-5 text-rose-700 shrink-0" />
          <div>
            <div className="font-black text-rose-900">World Model Graph Unavailable</div>
            <div className="text-[11px] text-slate-900">{error}</div>
          </div>
        </div>
      )}

      {/* Main Canvas Viewport */}
      {!isLoading && (
        <div className="relative w-full h-[640px] rounded-2xl overflow-hidden bg-white border border-slate-200 shadow-sm">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background color="#cbd5e1" gap={20} size={1} />
            <Controls className="bg-white border border-slate-300 text-slate-800 fill-slate-800 rounded-xl shadow-sm" />
            <MiniMap
              nodeColor={(node) => {
                const typeStr = String(node.data?.nodeType || '').toUpperCase();
                if (typeStr.includes('ENTITY')) return '#6366f1';
                if (typeStr.includes('OBSERVATION')) return '#0284c7';
                if (typeStr.includes('EVIDENCE')) return '#10b981';
                if (typeStr.includes('GAP')) return '#d97706';
                if (typeStr.includes('RECOMMENDATION')) return '#059669';
                return '#64748b';
              }}
              maskColor="rgba(241, 245, 249, 0.7)"
              className="bg-white border border-slate-300 rounded-xl shadow-sm"
            />
          </ReactFlow>

          {/* Selected Node Details Drawer */}
          {selectedNodeData && (
            <div className="absolute top-4 right-4 w-84 p-4 rounded-2xl bg-white/95 border border-slate-300 backdrop-blur-md shadow-lg space-y-3 z-50 max-h-[550px] overflow-y-auto font-sans">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="text-xs font-black uppercase text-[#0d2247]">
                  Node Telemetry Inspector
                </span>
                <button
                  onClick={() => setSelectedNodeData(null)}
                  className="text-xs font-black text-slate-500 hover:text-slate-900"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-600 font-bold">Class:</span>
                  <span className="text-slate-900 font-black">{selectedNodeData.nodeType}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900 text-emerald-400 font-mono text-[11px] border border-slate-800">
                  <pre className="overflow-x-auto whitespace-pre-wrap font-bold">
                    {JSON.stringify(selectedNodeData.raw, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Ontological Legend */}
          <div className="absolute bottom-4 left-4 p-3.5 rounded-xl bg-white/95 border border-slate-300 text-[10px] space-y-1.5 backdrop-blur-sm z-10 shadow-sm font-sans font-bold">
            <div className="font-black text-[#0d2247] uppercase mb-1">Ontology Legend</div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
              <span className="text-slate-900">Lunar Entity (Persistent Region)</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-600" />
              <span className="text-slate-900">Observation Stream</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
              <span className="text-slate-900">Physics Evidence & Verification</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-600" />
              <span className="text-slate-900">Knowledge Gap</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-600" />
              <span className="text-slate-900">World Model Hypothesis</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
