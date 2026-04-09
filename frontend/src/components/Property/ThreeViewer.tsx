/**
 * ThreeViewer — GLB model viewer. Minimal chrome.
 * No bouncing, no pulsing glow. Just the model.
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls, useGLTF, Environment, Center, Html } from '@react-three/drei';
import { useState, Suspense } from 'react';

interface ThreeViewerProps {
  modelUrl: string;
}

function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return (
    <Center>
      <primitive object={scene} />
    </Center>
  );
}

function Loader() {
  return (
    <Html center>
      <div style={{
        fontFamily: "'Satoshi', sans-serif",
        fontSize: '11px',
        fontWeight: 500,
        color: '#5c5856',
        letterSpacing: '0.08em',
        textTransform: 'uppercase' as const,
      }}>
        Loading model…
      </div>
    </Html>
  );
}

export default function ThreeViewer({ modelUrl }: ThreeViewerProps) {
  const [autoRotate, setAutoRotate] = useState(true);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#0e0e0e' }}>
      <Canvas
        camera={{ position: [3, 2, 3], fov: 50 }}
        gl={{ antialias: true, alpha: false }}
        style={{ background: '#0e0e0e' }}
      >
        <Suspense fallback={<Loader />}>
          <ambientLight intensity={0.4} />
          <directionalLight position={[5, 5, 5]} intensity={0.8} />
          <Model url={modelUrl} />
          <Environment preset="city" />
        </Suspense>
        <OrbitControls
          autoRotate={autoRotate}
          autoRotateSpeed={1}
          enableDamping
          dampingFactor={0.04}
          maxPolarAngle={Math.PI / 1.5}
          minDistance={1}
          maxDistance={10}
        />
      </Canvas>

      <button
        className="btn-chip"
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '12px',
          cursor: 'pointer',
        }}
        onClick={() => setAutoRotate(!autoRotate)}
      >
        {autoRotate ? 'Pause' : 'Rotate'}
      </button>
    </div>
  );
}
