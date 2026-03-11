/**
 * Manifest types and validators for Blender MCP exports
 */

import { z } from 'zod';

/**
 * Zod schema for manifest validation
 */
export const BlenderManifestSchema = z.object({
  version: z.string(),
  timestamp: z.number(),
  slug: z.string(),
  objects: z.array(z.object({
    id: z.string(),
    name: z.string(),
    type: z.string(),
    location: z.tuple([z.number(), z.number(), z.number()]),
    rotation: z.tuple([z.number(), z.number(), z.number()]),
    scale: z.tuple([z.number(), z.number(), z.number()]),
    dimensions: z.tuple([z.number(), z.number(), z.number()]),
    visible: z.boolean(),
    materials: z.array(z.string()).optional(),
    camera: z.object({
      lens: z.number(),
      sensor_width: z.number(),
      sensor_height: z.number()
    }).optional(),
    light: z.object({
      type: z.string(),
      energy: z.number(),
      color: z.tuple([z.number(), z.number(), z.number()])
    }).optional()
  })),
  cameras: z.array(z.object({
    name: z.string(),
    location: z.tuple([z.number(), z.number(), z.number()]),
    rotation: z.tuple([z.number(), z.number(), z.number()]),
    lens: z.number()
  })),
  lights: z.array(z.object({
    name: z.string(),
    type: z.string(),
    energy: z.number(),
    color: z.tuple([z.number(), z.number(), z.number()]),
    location: z.tuple([z.number(), z.number(), z.number()])
  })),
  world: z.object({
    name: z.string(),
    color: z.tuple([z.number(), z.number(), z.number()]).optional()
  }),
  render_settings: z.object({
    resolution_x: z.number(),
    resolution_y: z.number(),
    engine: z.string()
  }),
  bounds: z.object({
    min: z.tuple([z.number(), z.number(), z.number()]),
    max: z.tuple([z.number(), z.number(), z.number()]),
    center: z.tuple([z.number(), z.number(), z.number()]),
    size: z.tuple([z.number(), z.number(), z.number()])
  }),
  units: z.object({
    system: z.string(),
    scale_length: z.number()
  }),
  dependencies: z.array(z.string())
});

/**
 * Type for Blender manifest
 */
export type BlenderManifest = z.infer<typeof BlenderManifestSchema>;

/**
 * Type for manifest object
 */
export type ManifestObject = BlenderManifest['objects'][number];

/**
 * Type for manifest camera
 */
export type ManifestCamera = BlenderManifest['cameras'][number];

/**
 * Type for manifest light
 */
export type ManifestLight = BlenderManifest['lights'][number];

/**
 * Validate a manifest object
 * 
 * @param data - Data to validate
 * @returns Validated manifest or throws error
 */
export function validateManifest(data: unknown): BlenderManifest {
  return BlenderManifestSchema.parse(data);
}

/**
 * Safely validate a manifest object
 * 
 * @param data - Data to validate
 * @returns Object with success flag and result or error
 */
export function safeValidateManifest(data: unknown): 
  { success: true; data: BlenderManifest } | { success: false; error: z.ZodError } {
  const result = BlenderManifestSchema.safeParse(data);
  
  if (result.success) {
    return { success: true, data: result.data };
  } else {
    return { success: false, error: result.error };
  }
}

/**
 * Get object by name from manifest
 * 
 * @param manifest - The manifest
 * @param name - Object name
 * @returns Object or undefined
 */
export function getObjectByName(manifest: BlenderManifest, name: string): ManifestObject | undefined {
  return manifest.objects.find(obj => obj.name === name);
}

/**
 * Get object by ID from manifest
 * 
 * @param manifest - The manifest
 * @param id - Object ID
 * @returns Object or undefined
 */
export function getObjectById(manifest: BlenderManifest, id: string): ManifestObject | undefined {
  return manifest.objects.find(obj => obj.id === id);
}

/**
 * Get camera by name from manifest
 * 
 * @param manifest - The manifest
 * @param name - Camera name
 * @returns Camera or undefined
 */
export function getCameraByName(manifest: BlenderManifest, name: string): ManifestCamera | undefined {
  return manifest.cameras.find(cam => cam.name === name);
}

/**
 * Get light by name from manifest
 * 
 * @param manifest - The manifest
 * @param name - Light name
 * @returns Light or undefined
 */
export function getLightByName(manifest: BlenderManifest, name: string): ManifestLight | undefined {
  return manifest.lights.find(light => light.name === name);
}

/**
 * Calculate scene center from bounds
 * 
 * @param manifest - The manifest
 * @returns Center position
 */
export function getSceneCenter(manifest: BlenderManifest): [number, number, number] {
  return manifest.bounds.center;
}

/**
 * Calculate scene radius from bounds
 * 
 * @param manifest - The manifest
 * @returns Radius (half of largest dimension)
 */
export function getSceneRadius(manifest: BlenderManifest): number {
  const size = manifest.bounds.size;
  return Math.max(...size) / 2;
}