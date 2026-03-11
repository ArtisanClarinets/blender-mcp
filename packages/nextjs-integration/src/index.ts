/**
 * Blender MCP Next.js Integration
 * 
 * Provides utilities for loading and using Blender MCP exports in Next.js 16 applications.
 */

export * from './manifest';
export * from './r3f';

import { BlenderManifest } from './manifest';

/**
 * Load a Blender MCP manifest from the public directory
 * 
 * @param slug - The scene slug/identifier
 * @returns The parsed manifest
 */
export async function loadBlenderManifest(slug: string): Promise<BlenderManifest> {
  const response = await fetch(`/3d/${slug}/manifest.json`);
  
  if (!response.ok) {
    throw new Error(`Failed to load manifest for "${slug}": ${response.statusText}`);
  }
  
  const data = await response.json();
  return data as BlenderManifest;
}

/**
 * Resolve public asset paths for a scene
 * 
 * @param slug - The scene slug/identifier
 * @returns Object with resolved paths
 */
export function resolvePublicAssetPaths(slug: string): {
  model: string;
  preview: string;
  manifest: string;
  components: string;
} {
  return {
    model: `/3d/${slug}/model.glb`,
    preview: `/3d/${slug}/preview.png`,
    manifest: `/3d/${slug}/manifest.json`,
    components: `/3d/${slug}/components`
  };
}

/**
 * Get scene bounds from manifest
 * 
 * @param manifest - The Blender manifest
 * @returns Bounds information
 */
export function getSceneBounds(manifest: BlenderManifest): {
  min: [number, number, number];
  max: [number, number, number];
  center: [number, number, number];
  size: [number, number, number];
} {
  return manifest.bounds;
}

/**
 * Get default camera from manifest
 * 
 * @param manifest - The Blender manifest
 * @returns Camera information or undefined
 */
export function getDefaultCamera(manifest: BlenderManifest) {
  return manifest.cameras[0];
}

/**
 * Get all lights from manifest
 * 
 * @param manifest - The Blender manifest
 * @returns Array of light information
 */
export function getLights(manifest: BlenderManifest) {
  return manifest.lights;
}

/**
 * Preload scene assets
 * 
 * Call this function to preload assets before rendering
 * 
 * @param slug - The scene slug/identifier
 */
export function preloadSceneAssets(slug: string): void {
  // Preload manifest
  const manifestPath = `/3d/${slug}/manifest.json`;
  
  // Preload model
  const modelPath = `/3d/${slug}/model.glb`;
  
  // Use Next.js preload if available
  if (typeof window !== 'undefined') {
    // Preload manifest
    const manifestLink = document.createElement('link');
    manifestLink.rel = 'preload';
    manifestLink.as = 'fetch';
    manifestLink.href = manifestPath;
    document.head.appendChild(manifestLink);
    
    // Preload model
    const modelLink = document.createElement('link');
    modelLink.rel = 'preload';
    modelLink.as = 'fetch';
    modelLink.href = modelPath;
    document.head.appendChild(modelLink);
  }
}