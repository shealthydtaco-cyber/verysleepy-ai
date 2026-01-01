"use client"

import { useMemo, useRef } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { Sphere, MeshDistortMaterial, Float, PerspectiveCamera } from "@react-three/drei"
import * as THREE from "three"

type OrbState = "idle" | "listening" | "speaking"

interface AIOrbProps {
  state: OrbState
  intensity?: number
}

function EtherealOrb({ state, intensity = 1 }: AIOrbProps) {
  const meshRef = useRef<THREE.Mesh>(null!)
  const materialRef = useRef<any>(null!)

  // Define animation parameters based on state
  const stateConfig = useMemo(() => {
    switch (state) {
      case "listening":
        return {
          distort: 0.6,
          speed: 4,
          color: "#3b82f6", // Electric Blue
          emissive: "#1d4ed8",
          scale: 1.1,
        }
      case "speaking":
        return {
          distort: 0.4,
          speed: 8,
          color: "#ec4899", // Pulsing Pink/Purple
          emissive: "#be185d",
          scale: 1.2,
        }
      default: // idle
        return {
          distort: 0.3,
          speed: 1.5,
          color: "#ffffff", // Ethereal White/Silver
          emissive: "#94a3b8",
          scale: 1,
        }
    }
  }, [state])

  useFrame((stateContext) => {
    const t = stateContext.clock.getElapsedTime()

    // Smooth transitions for material properties
    if (materialRef.current) {
      materialRef.current.distort = THREE.MathUtils.lerp(
        materialRef.current.distort,
        stateConfig.distort * intensity,
        0.05,
      )
      materialRef.current.speed = THREE.MathUtils.lerp(materialRef.current.speed, stateConfig.speed, 0.05)
      materialRef.current.color.lerp(new THREE.Color(stateConfig.color), 0.05)
      materialRef.current.emissive.lerp(new THREE.Color(stateConfig.emissive), 0.05)
    }

    // Floating animation
    if (meshRef.current) {
      const targetScale = stateConfig.scale + (state === "speaking" ? Math.sin(t * 10) * 0.05 : 0)
      meshRef.current.scale.setScalar(THREE.MathUtils.lerp(meshRef.current.scale.x, targetScale, 0.1))
    }
  })

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
      <Sphere ref={meshRef} args={[1, 64, 64]}>
        <MeshDistortMaterial
          ref={materialRef}
          color={stateConfig.color}
          emissive={stateConfig.emissive}
          emissiveIntensity={0.5}
          roughness={0}
          metalness={1}
          distort={stateConfig.distort}
          speed={stateConfig.speed}
          transparent
          opacity={0.8}
        />
      </Sphere>

      {/* Subtle outer glow layer */}
      <Sphere args={[1.05, 32, 32]}>
        <meshBasicMaterial color={stateConfig.color} transparent opacity={0.1} wireframe />
      </Sphere>
    </Float>
  )
}

export function AIOrbContainer({ state }: { state: OrbState }) {
  return (
    <div className="relative w-full h-[400px] flex items-center justify-center overflow-hidden">
      {/* Glass Bubble Wrapper */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-64 h-64 rounded-full border border-white/10 bg-white/5 backdrop-blur-xl shadow-[inset_0_0_40px_rgba(255,255,255,0.1)]" />
      </div>

      <Canvas className="w-full h-full">
        <PerspectiveCamera makeDefault position={[0, 0, 4]} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} />
        <pointLight position={[-10, -10, -10]} color="#3b82f6" intensity={1} />

        <EtherealOrb state={state} />

        {/* Particle System for background ambience */}
        <Particles
          count={50}
          color={state === "listening" ? "#3b82f6" : state === "speaking" ? "#ec4899" : "#ffffff"}
        />
      </Canvas>
    </div>
  )
}

function Particles({ count, color }: { count: number; color: string }) {
  const points = useMemo(() => {
    const p = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * 6
      p[i * 3 + 1] = (Math.random() - 0.5) * 6
      p[i * 3 + 2] = (Math.random() - 0.5) * 6
    }
    return p
  }, [count])

  const pointsRef = useRef<THREE.Points>(null!)

  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y += 0.001
      pointsRef.current.rotation.x += 0.0005
    }
  })

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={points} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color={color}
        transparent
        opacity={0.4}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}
