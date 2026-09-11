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
import { Network, Filter, Info, RefreshCw, Globe, Layers, Activity, Shield } from 'lucide-react';
import { api } from '../services/api';

export const EntityGraph: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchGraph = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getFullGraph();
      
      // Transform nodes with customized styles & badges
      const styledNodes: Node[] = data.nodes.map((n: any) => {
        let bgColor = '#1e293b';
        let borderColor = '#334155';
        let textColor = '#f1f5f9';

        if (n.type === 'LunarEntity') {
          bgColor = '#1e1b4b';
          borderColor = '#6366f1';
          textColor = '#c7d2fe';
        } else if (n.type === 'Observation') {
          bgColor = '#082f49';
          borderColor = '#0284c7';
          textColor = '#bae6fd';
        } else if (n.type === 'PhysicsEvidence') {
          bgColor = '#064e3b';
          borderColor = '#059669';
          textColor = '#a7f3d0';
        } else if (n.type === 'Sensor') {
          bgColor = '#312e81';
          borderColor = '#818cf8';
        } else if (n.type === 'Hypothesis') {
          bgColor = '#18181b';
          borderColor = '#71717a';
        }

        return {
          id: n.id,
          type: 'default',
          position: n.position,
          data: {
            label: (
              <div className="p-1 font-mono text-left">
                <div className="text-[9px] uppercase tracking-wider text-lunar-400 font-bold">
                  {n.type}
                </div>
                <div className="text-xs font-bold truncate max-w-[160px]">{n.data.label}</div>
                {n.data.confidence !== undefined && (
                  <div className="text-[10px] text-space-emerald mt-0.5">
                    Conf: {Math.round(n.data.confidence * 100)}%
                  </div>
                )}
              </div>
            ),
            raw: n.data,
            nodeType: n.type,
          },
          style: {
            background: bgColor,
            color: textColor,
            border: `1px solid ${borderColor}`,
            borderRadius: '8px',
            width: 190,
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          },
        };
      });

      const styledEdges: Edge[] = data.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: e.animated,
        style: e.style || { stroke: '#38bdf8', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 12,
          height: 12,
          color: e.style?.stroke || '#38bdf8',
        },
        labelStyle: { fill: '#94a3b8', fontSize: 9, fontFamily: 'monospace' },
        labelBgStyle: { fill: '#0b0f17', fillOpacity: 0.85 },
      }));

      setNodes(styledNodes);
      setEdges(styledEdges);
    } catch (err) {
      console.error('Failed to load graph', err);
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
    <div className="space-y-4 font-mono">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-lunar-50 flex items-center space-x-2">
            <Network className="w-5 h-5 text-space-cyan" />
            <span>Lunar Entity Knowledge Graph</span>
          </h1>
          <p className="text-xs text-lunar-400">
            NetworkX relational ontology linking persistent lunar entities, multi-modal sensor streams, physics evidence, and hypotheses.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchGraph}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-lunar-900 hover:bg-lunar-800 text-xs text-space-cyan border border-lunar-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Graph</span>
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div className="relative w-full h-[640px] rounded-xl overflow-hidden bg-lunar-950 border border-lunar-700/60 shadow-2xl">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
        >
          <Background color="#1e293b" gap={20} size={1} />
          <Controls className="bg-lunar-900 border border-lunar-700 text-lunar-200 fill-lunar-200" />
          <MiniMap
            nodeColor={(node) => {
              if (node.data.nodeType === 'LunarEntity') return '#6366f1';
              if (node.data.nodeType === 'Observation') return '#0284c7';
              if (node.data.nodeType === 'PhysicsEvidence') return '#10b981';
              return '#475569';
            }}
            maskColor="rgba(7, 10, 15, 0.85)"
            className="bg-lunar-900 border border-lunar-700 rounded-lg"
          />
        </ReactFlow>

        {/* Selected Node Details Drawer */}
        {selectedNodeData && (
          <div className="absolute top-4 right-4 w-80 p-4 rounded-xl bg-lunar-900/95 border border-lunar-700 backdrop-blur-md shadow-2xl space-y-3 z-50">
            <div className="flex items-center justify-between border-b border-lunar-800 pb-2">
              <span className="text-xs font-bold uppercase text-space-cyan">
                Node Inspector
              </span>
              <button
                onClick={() => setSelectedNodeData(null)}
                className="text-xs text-lunar-400 hover:text-lunar-100"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-lunar-400">Class:</span>
                <span className="text-lunar-100 font-bold">{selectedNodeData.nodeType}</span>
              </div>
              <div className="p-2 rounded bg-lunar-950 border border-lunar-800 text-[11px] text-lunar-300">
                <pre className="overflow-x-auto">
                  {JSON.stringify(selectedNodeData.raw, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 p-3 rounded-lg bg-lunar-900/90 border border-lunar-800 text-[10px] space-y-1.5 backdrop-blur-sm z-10">
          <div className="font-bold text-lunar-300 uppercase mb-1">Ontology Legend</div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
            <span className="text-lunar-300">Lunar Entity (Persistent Region)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
            <span className="text-lunar-300">Observation Stream</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-lunar-300">Physics Evidence & Verification</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
            <span className="text-lunar-300">World Model Hypothesis</span>
          </div>
        </div>
      </div>
    </div>
  );
};
