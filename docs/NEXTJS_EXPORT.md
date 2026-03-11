# Next.js 16 Export Guide

## Overview

Blender MCP can export scenes directly into Next.js 16 applications with automatic component generation.

## Output Structure

When you export a scene bundle, the following structure is created:

```
your-next-app/public/3d/<slug>/
├── model.glb              # Exported 3D model (Draco compressed)
├── preview.png            # Rendered preview image
├── manifest.json          # Scene metadata
└── components/            # (Optional) React Three Fiber components
    ├── Scene.tsx
    ├── Model.tsx
    └── Camera.tsx
```

## Usage

### Basic Export

```python
result = call_tool("export_scene_bundle", {
    "slug": "dungeon-scene",
    "nextjs_project_root": "/path/to/next-app",
    "mode": "scene",
    "generate_r3f": True
})
```

### Parameters

- **slug** (required): Unique identifier for the scene
- **nextjs_project_root** (required): Absolute path to Next.js project
- **mode** (optional): `"scene"` or `"assets"` (default: `"scene"`)
- **generate_r3f** (optional): Generate React Three Fiber components (default: `False`)

## Manifest Format

The `manifest.json` file contains:

```json
{
  "version": "1.0.0",
  "timestamp": 1234567890,
  "slug": "dungeon-scene",
  "objects": [
    {
      "id": "uuid",
      "name": "Cube",
      "type": "MESH",
      "location": [0, 0, 0],
      "rotation": [0, 0, 0],
      "scale": [1, 1, 1],
      "dimensions": [2, 2, 2],
      "visible": true
    }
  ],
  "cameras": [
    {
      "name": "Camera",
      "location": [7, -7, 5],
      "rotation": [1.1, 0, 0.8],
      "lens": 50
    }
  ],
  "lights": [
    {
      "name": "Light",
      "type": "SUN",
      "energy": 3,
      "color": [1, 1, 1],
      "location": [5, 5, 10]
    }
  ],
  "world": {
    "name": "World",
    "color": [0.05, 0.05, 0.05]
  },
  "render_settings": {
    "resolution_x": 1920,
    "resolution_y": 1080,
    "engine": "CYCLES"
  },
  "bounds": {
    "min": [-5, -5, 0],
    "max": [5, 5, 10],
    "center": [0, 0, 5],
    "size": [10, 10, 10]
  },
  "units": {
    "system": "METRIC",
    "scale_length": 1.0
  },
  "dependencies": []
}
```

## React Three Fiber Components

When `generate_r3f=True`, the following components are generated:

### Model.tsx

```tsx
import { useGLTF } from '@react-three/drei'
import { forwardRef } from 'react'

export const Model = forwardRef((props, ref) => {
  const { scene } = useGLTF('/3d/dungeon-scene/model.glb')
  return <primitive ref={ref} object={scene} {...props} />
})

Model.displayName = 'Model'

useGLTF.preload('/3d/dungeon-scene/model.glb')
```

### Camera.tsx

```tsx
import { PerspectiveCamera } from '@react-three/drei'

export const Camera = () => {
  return (
    <PerspectiveCamera
      name="Camera"
      makeDefault
      position={[7, -7, 5]}
      rotation={[1.1, 0, 0.8]}
      fov={50}
    />
  )
}
```

### Scene.tsx

```tsx
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import { Model } from './Model'
import { Camera } from './Camera'

export const Scene = () => {
  return (
    <Canvas>
      <Camera />
      <ambientLight intensity={0.5} />
      <Model />
      <OrbitControls />
    </Canvas>
  )
}
```

## Next.js Page Example

```tsx
// app/3d-scene/page.tsx
import { Scene } from '@/components/3d/Scene'

export default function ScenePage() {
  return (
    <div className="w-full h-screen">
      <Scene />
    </div>
  )
}
```

## Dynamic Import (Recommended)

For better performance, use dynamic imports:

```tsx
// app/3d-scene/page.tsx
import dynamic from 'next/dynamic'

const Scene = dynamic(
  () => import('@/components/3d/Scene').then(mod => mod.Scene),
  { ssr: false, loading: () => <p>Loading 3D Scene...</p> }
)

export default function ScenePage() {
  return (
    <div className="w-full h-screen">
      <Scene />
    </div>
  )
}
```

## Cache Invalidation

When you re-export a scene, the files are overwritten. To ensure browsers load the new version:

1. **Change the slug** for major updates
2. **Use version query parameters**:
   ```tsx
   useGLTF('/3d/scene/model.glb?v=2')
   ```
3. **Configure Next.js revalidation**:
   ```tsx
   export const revalidate = 60 // seconds
   ```

## Best Practices

1. **Use meaningful slugs**: `"hero-section"`, `"product-showcase"`
2. **Optimize before export**: Apply modifiers, remove unused data
3. **Test in development**: Verify the scene loads correctly
4. **Use Draco compression**: Enabled by default for smaller files
5. **Generate previews**: Helps with content management

## Troubleshooting

### Model not appearing
- Check browser console for GLTFLoader errors
- Verify file paths are correct
- Ensure `public/3d/` directory is accessible

### Performance issues
- Enable Draco compression
- Reduce polygon count before export
- Use `useGLTF.preload()` for faster loading

### CORS errors
- Ensure files are served from the same origin
- Check Next.js `next.config.js` headers

## Integration Package

For advanced use cases, install the optional Next.js integration package:

```bash
npm install @blender-mcp/nextjs-integration
```

This provides:
- TypeScript types for manifests
- Helper hooks for loading scenes
- Utilities for scene management