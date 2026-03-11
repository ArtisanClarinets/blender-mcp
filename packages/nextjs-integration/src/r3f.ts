/**
 * React Three Fiber components for Blender MCP scenes
 * 
 * Note: These are type definitions and factory functions.
 * Actual JSX components should be created in your Next.js app.
 */

import { BlenderManifest, ManifestCamera, ManifestLight } from './manifest';

/**
 * Props for Model component
 */
export interface ModelProps {
  /** URL to the GLB model */
  url: string;
  /** Optional scale */
  scale?: number | [number, number, number];
  /** Optional position */
  position?: [number, number, number];
  /** Optional rotation */
  rotation?: [number, number, number];
}

/**
 * Props for Camera component
 */
export interface CameraProps {
  /** Camera configuration from manifest */
  camera?: ManifestCamera;
  /** Optional FOV override */
  fov?: number;
  /** Make this the default camera */
  makeDefault?: boolean;
}

/**
 * Props for Light component
 */
export interface LightProps {
  /** Light configuration from manifest */
  light: ManifestLight;
}

/**
 * Props for Scene component
 */
export interface SceneProps {
  /** The Blender manifest */
  manifest: BlenderManifest;
  /** URL to the GLB model */
  modelUrl: string;
  /** Optional children */
  children?: any;
  /** Canvas props */
  canvasProps?: any;
  /** Show orbit controls */
  controls?: boolean;
  /** Show environment */
  environment?: boolean;
}

/**
 * Generate Model component code as string
 * 
 * @param slug - Scene slug
 * @returns Component code
 */
export function generateModelComponent(slug: string): string {
  return `
import { useGLTF } from '@react-three/drei'
import { forwardRef } from 'react'

export const Model = forwardRef((props, ref) => {
  const { scene } = useGLTF('/3d/${slug}/model.glb')
  return <primitive ref={ref} object={scene} {...props} />
})

Model.displayName = 'Model'

useGLTF.preload('/3d/${slug}/model.glb')
`;
}

/**
 * Generate Camera component code as string
 * 
 * @param camera - Camera from manifest
 * @returns Component code
 */
export function generateCameraComponent(camera?: ManifestCamera): string {
  if (!camera) {
    return `
import { PerspectiveCamera } from '@react-three/drei'

export const Camera = () => (
  <PerspectiveCamera makeDefault position={[7, -7, 5]} fov={50} />
)
`;
  }
  
  return `
import { PerspectiveCamera } from '@react-three/drei'

export const Camera = () => (
  <PerspectiveCamera
    makeDefault
    position={[${camera.location.join(', ')}]}
    rotation={[${camera.rotation.join(', ')}]}
    fov={${camera.lens}}
  />
)
`;
}

/**
 * Generate Scene component code as string
 * 
 * @param slug - Scene slug
 * @param manifest - Scene manifest
 * @returns Component code
 */
export function generateSceneComponent(slug: string, manifest: BlenderManifest): string {
  const hasLights = manifest.lights.length > 0;
  
  return `
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import { Model } from './Model'
import { Camera } from './Camera'

export const Scene = () => {
  return (
    <Canvas shadows>
      <Camera />
      <ambientLight intensity={0.5} />
${hasLights ? manifest.lights.map(l => `      <Light light={${JSON.stringify(l)}} />`).join('\n') : ''}
      <Model />
      <OrbitControls />
    </Canvas>
  )
}
`;
}

/**
 * Generate all R3F components for a scene
 * 
 * @param slug - Scene slug
 * @param manifest - Scene manifest
 * @returns Object with component codes
 */
export function generateR3FComponents(slug: string, manifest: BlenderManifest) {
  return {
    Model: generateModelComponent(slug),
    Camera: generateCameraComponent(manifest.cameras[0]),
    Scene: generateSceneComponent(slug, manifest)
  };
}