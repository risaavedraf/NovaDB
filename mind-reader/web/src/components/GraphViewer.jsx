import React, { useEffect, useState, useRef } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

export default function GraphViewer() {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeContext, setNodeContext] = useState(null);
  const fgRef = useRef();

  useEffect(() => {
    // Parche #3: URL Dinamica desde el framework, con fallback a tu localhost de dev
    const apiUrl = import.meta.env?.PUBLIC_API_URL || 'http://localhost:8000';
    
    // Parche #2: Peticion firmada con la llave fuerte local
    fetch(`${apiUrl}/api/graph`, {
        headers: {
            'x-api-key': 'nova-secret-key-2026'
        }
    })
      .then(res => {
          if(!res.ok) throw new Error("Acceso denegado: API Key rechazada.");
          return res.json();
      })
      .then(json => {
        setData(json);
        // Expandir el universo visual forzando que se separen
        setTimeout(() => {
            if (fgRef.current) {
                fgRef.current.d3Force("charge").strength(-400);
                fgRef.current.d3Force("link").distance(60);
            }
        }, 100);
      })
      .catch(err => console.error("Error cargando mente de Nova:", err));
  }, []);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    setNodeContext(null);
    
    // Traer el contexto profundo (Jerarquia)
    const apiUrl = import.meta.env?.PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/node/${node.id}`, {
      headers: { 'x-api-key': 'nova-secret-key-2026' }
    })
    .then(res => res.json())
    .then(json => setNodeContext(json));

    // Zoom de la camara directo a la memoria o concepto 
    const distance = 60;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
    
    if (fgRef.current) {
        fgRef.current.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
          node,
          2000 // ms de animacion fluida
        );
    }
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', backgroundColor: '#050505', color: '#0ff' }}>
      
      {/* Lienzo WebGL Universo Mental */}
      <div style={{ flex: 1 }}>
        <ForceGraph3D
          ref={fgRef}
          graphData={data}
          nodeAutoColorBy="group"
          nodeVal="val"
          nodeLabel="name"
          onNodeClick={handleNodeClick}
          linkWidth="value"
          linkLabel="label"
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={d => Math.max(0.005, d.sim * 0.01)}
          linkColor={d => `rgba(0, 255, 255, ${Math.max(0.3, d.sim)})`} // Piso de 0.3 de opacidad para no perder las hebras
          backgroundColor="#020205" // Deep dark eslavo
        />
      </div>

      {/* Córtex Inspector (Panel lateral Glassmorphism) */}
      {selectedNode && (
        <div style={{
          position: 'absolute', top: 20, right: 20, width: 320, 
          backgroundColor: 'rgba(10, 15, 25, 0.75)', padding: '25px', 
          borderRadius: '12px', backdropFilter: 'blur(12px)',
          border: '1px solid rgba(0, 255, 255, 0.3)', 
          boxShadow: '0 0 30px rgba(0, 255, 255, 0.1)'
        }}>
          <div style={{ 
            display: 'inline-block', padding: '4px 8px', borderRadius: '4px',
            backgroundColor: selectedNode.group === 1 ? 'rgba(255,0,0,0.2)' : (selectedNode.group === 2 ? 'rgba(0,255,0,0.2)' : 'rgba(0,0,255,0.2)'),
            color: selectedNode.group === 1 ? '#ff4d4d' : (selectedNode.group === 2 ? '#4dff4d' : '#4d4dff'),
            fontSize: '12px', fontWeight: 'bold', marginBottom: '10px', textTransform: 'uppercase'
          }}>
            {selectedNode.tipo}
          </div>
          
          <h2 style={{ margin: '0 0 15px', fontSize: '18px', color: '#e0e0e0', fontWeight: '500' }}>
            {selectedNode.name}
          </h2>

          {nodeContext && (
            <div style={{ fontSize: '13px', color: '#ccc' }}>
              {/* Estructura Jerárquica */}
              <div style={{ marginBottom: '15px' }}>
                <b style={{ color: '#0ff', fontSize: '11px', textTransform: 'uppercase' }}>Padres (Ancestros)</b>
                {nodeContext.padres.length > 0 ? (
                  <ul style={{ paddingLeft: '15px', marginTop: '5px' }}>
                    {nodeContext.padres.map(p => <li key={p.id}>{p.text.substring(0, 40)}...</li>)}
                  </ul>
                ) : <p style={{ fontSize: '11px', opacity: 0.5 }}>- Raíz (Sin padres)</p>}
              </div>

              <div style={{ marginBottom: '15px' }}>
                <b style={{ color: '#0ff', fontSize: '11px', textTransform: 'uppercase' }}>Hijos (Descendientes)</b>
                {nodeContext.hijos.length > 0 ? (
                  <ul style={{ paddingLeft: '15px', marginTop: '5px' }}>
                    {nodeContext.hijos.map(h => <li key={h.id}>{h.text.substring(0, 40)}...</li>)}
                  </ul>
                ) : <p style={{ fontSize: '11px', opacity: 0.5 }}>- Hoja (Sin hijos)</p>}
              </div>

              <div style={{ marginBottom: '15px' }}>
                <b style={{ color: '#0ff', fontSize: '11px', textTransform: 'uppercase' }}>Vecindario Semántico</b>
                {nodeContext.vecinos.length > 0 ? (
                  <ul style={{ paddingLeft: '15px', marginTop: '5px' }}>
                    {nodeContext.vecinos.map(v => <li key={v.id}>{v.text.substring(0, 40)}...</li>)}
                  </ul>
                ) : <p style={{ fontSize: '11px', opacity: 0.5 }}>- Aislado</p>}
              </div>
            </div>
          )}
          
          <div style={{ marginTop: 20, fontSize: '11px', color: '#666', fontFamily: 'monospace' }}>
            <p style={{ margin: '5px 0' }}>UUID: {selectedNode.id}</p>
            <p style={{ margin: '5px 0' }}>⚡ RECALL HITS: {selectedNode.accesos}</p>
          </div>
          
          <button 
            onClick={() => setSelectedNode(null)}
            style={{ 
              marginTop: 25, width: '100%', padding: '10px', 
              background: 'transparent', color: '#0ff', 
              border: '1px solid rgba(0, 255, 255, 0.5)', borderRadius: '6px', 
              cursor: 'pointer', fontWeight: 'bold', transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.target.style.background = 'rgba(0, 255, 255, 0.1)'}
            onMouseOut={(e) => e.target.style.background = 'transparent'}
          >
            Cerrar Inspector
          </button>
        </div>
      )}
      
      {/* Watermark de MindReader */}
      <div style={{ position: 'absolute', bottom: 20, left: 20, color: 'rgba(255,255,255,0.2)', fontSize: '24px', fontWeight: 'bold', pointerEvents: 'none' }}>
        NovaDB <span style={{ fontWeight: 'normal', color: 'rgba(0,255,255,0.4)' }}>MindReader</span>
      </div>
    </div>
  );
}
