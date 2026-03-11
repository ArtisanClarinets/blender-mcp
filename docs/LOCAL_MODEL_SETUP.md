# Local 3D Model Generation Setup Guide

This guide explains how to set up and use local 3D generation models with Blender MCP.

## Table of Contents

1. [Overview](#overview)
2. [Supported Models](#supported-models)
3. [Setup Instructions](#setup-instructions)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Troubleshooting](#troubleshooting)

## Overview

Blender MCP supports locally hosted 3D generation models, giving you:
- **Privacy**: Your data stays on your machine
- **Cost savings**: No API fees for unlimited generations
- **Customization**: Fine-tune models for your specific needs
- **Offline capability**: Generate 3D models without internet

## Supported Models

### 1. Hunyuan3D-2 (Recommended)
**Best for**: High-quality text/image-to-3D generation

**Features**:
- Text-to-3D generation
- Image-to-3D generation
- High-quality mesh output
- Fast inference

**Requirements**:
- NVIDIA GPU with 8GB+ VRAM (16GB recommended)
- Python 3.10+
- CUDA 11.8 or 12.1

### 2. InstantMesh
**Best for**: Fast image-to-3D generation

**Features**:
- Very fast inference (~10 seconds)
- Good quality for simple objects
- Sparse-view reconstruction

**Requirements**:
- NVIDIA GPU with 6GB+ VRAM
- Python 3.9+

### 3. CRM (Convolutional Reconstruction Model)
**Best for**: Single image to 3D

**Features**:
- Novel view synthesis
- 360° reconstruction from single image
- Diffusion-based generation

**Requirements**:
- NVIDIA GPU with 8GB+ VRAM
- Python 3.10+

### 4. TRELLIS
**Best for**: High-quality structured 3D generation

**Features**:
- Structured latent representations
- High-quality mesh generation
- Multi-view consistency

**Requirements**:
- NVIDIA GPU with 12GB+ VRAM
- Python 3.10+

### 5. Zero123
**Best for**: Novel view synthesis

**Features**:
- View synthesis from single image
- 360° object understanding
- Foundation for other models

**Requirements**:
- NVIDIA GPU with 6GB+ VRAM
- Python 3.9+

## Setup Instructions

### Hunyuan3D-2 Setup

1. **Clone the repository**:
```bash
git clone https://github.com/tencent/Hunyuan3D-2.git
cd Hunyuan3D-2
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

4. **Download pretrained weights**:
```bash
# Weights download automatically on first run
# Or manually download from HuggingFace
huggingface-cli download tencent/Hunyuan3D-2 --local-dir ./weights
```

5. **Test installation**:
```bash
python gradio_app.py --server_port 8080
```

### InstantMesh Setup

1. **Clone the repository**:
```bash
git clone https://github.com/TencentARC/InstantMesh.git
cd InstantMesh
```

2. **Install dependencies**:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

3. **Download weights**:
```bash
# Download from HuggingFace
huggingface-cli download TencentARC/InstantMesh --local-dir ./weights
```

4. **Run server**:
```bash
python run.py --port 8080
```

### CRM Setup

1. **Clone the repository**:
```bash
git clone https://github.com/thu-ml/CRM.git
cd CRM
```

2. **Install dependencies**:
```bash
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

3. **Download weights**:
```bash
# Follow repository instructions for weight download
python download_weights.py
```

### TRELLIS Setup

1. **Clone the repository**:
```bash
git clone https://github.com/microsoft/TRELLIS.git
cd TRELLIS
```

2. **Install dependencies**:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

3. **Download weights**:
```bash
huggingface-cli download microsoft/TRELLIS --local-dir ./weights
```

## Configuration

### Blender Addon Preferences

1. **Open Blender Preferences**:
   - Edit > Preferences > Add-ons > Blender MCP

2. **Enable Local Model Server**:
   - Check "Enable Local Model Server"

3. **Configure Settings**:
   - **Model Type**: Select your installed model
   - **Model Path**: Path to the cloned repository
   - **Python Executable**: Path to the Python with dependencies installed (or leave empty for system Python)
   - **Server Port**: Port for the local server (default: 8080)
   - **Custom Launch Command**: (Optional) Override auto-generated launch command

4. **Save Preferences**:
   - Click "Save Preferences" at the bottom

### Example Configurations

**Hunyuan3D-2**:
- Model Type: `Hunyuan3D`
- Model Path: `/home/user/Hunyuan3D-2`
- Python Executable: `/home/user/Hunyuan3D-2/venv/bin/python`
- Server Port: `8080`

**InstantMesh**:
- Model Type: `InstantMesh`
- Model Path: `/home/user/InstantMesh`
- Python Executable: (empty - uses system Python)
- Server Port: `8080`

## Usage

### Starting the Local Server

**Method 1: Via Blender UI**
1. Open 3D View sidebar (press N)
2. Go to "BlenderMCP" tab
3. Click "Start Local Model"

**Method 2: Via Python**
```python
import bpy
bpy.ops.blendermcp.start_local_model()
```

**Method 3: Via MCP Command**
```python
result = call_tool("start_local_model_server", {})
```

### Generating 3D Models

Once the local server is running, you can use it through the MCP:

```python
# Generate from text
result = call_tool("generate_hunyuan3d_model", {
    "text_prompt": "A red sports car",
    "mode": "local"  # Use local server
})

# Check status
status = call_tool("get_local_model_status", {})
print(status)
```

### Stopping the Server

**Via Blender UI**:
1. Open 3D View sidebar
2. Click "Stop Local Model"

**Via MCP**:
```python
call_tool("stop_local_model_server", {})
```

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
- Ensure you installed all dependencies in the virtual environment
- Verify Python executable path is correct

**2. CUDA out of memory**
- Reduce batch size in model configuration
- Close other GPU-intensive applications
- Use a model with lower VRAM requirements

**3. Server won't start**
- Check if port is already in use: `lsof -i :8080`
- Verify model path is correct
- Check Blender's System Console for error messages

**4. Slow generation**
- Ensure GPU acceleration is enabled
- Check CUDA is properly installed: `nvidia-smi`
- Close unnecessary applications

### Performance Tips

1. **Use appropriate models**:
   - InstantMesh for quick drafts
   - Hunyuan3D for final quality
   - CRM for single-image reconstruction

2. **Optimize GPU usage**:
   - Close Blender viewport rendering during generation
   - Use smaller preview resolutions
   - Batch multiple generations

3. **Memory management**:
   - Restart server after many generations
   - Monitor GPU memory with `nvidia-smi`
   - Use models appropriate for your VRAM

### Model-Specific Tips

**Hunyuan3D**:
- Use descriptive prompts for best results
- Image-to-3D works best with clear, centered objects
- Enable "high_quality" mode for final renders

**InstantMesh**:
- Works best with 4-6 input views
- Use for quick prototyping
- Good for objects with clear silhouettes

**CRM**:
- Single image should show clear object
- White/neutral backgrounds work best
- Takes longer but produces detailed results

## Advanced Configuration

### Custom Launch Commands

For complex setups, use custom launch commands:

**Hunyuan3D with specific GPU**:
```
CUDA_VISIBLE_DEVICES=0 python gradio_app.py --server_port 8080
```

**InstantMesh with optimizations**:
```
python run.py --port 8080 --fp16 --mc_resolution 256
```

### Environment Variables

Set in Blender's Python console before starting:
```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
```

### Integration with Other Tools

The local server exposes a standard HTTP API that can be used by other tools:

```bash
# Example API call
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a red cube", "steps": 50}'
```

## Security Considerations

1. **Local Only**: By default, local servers only accept connections from localhost
2. **Firewall**: Ensure firewall allows Blender to communicate on the configured port
3. **Model Safety**: Local models don't filter content - use responsibly

## Getting Help

- **Blender MCP Issues**: https://github.com/ahujasid/blender-mcp/issues
- **Model-specific issues**: Check respective GitHub repositories
- **Community**: Blender MCP Discord

## Resources

- **Hunyuan3D-2**: https://github.com/tencent/Hunyuan3D-2
- **InstantMesh**: https://github.com/TencentARC/InstantMesh
- **CRM**: https://github.com/thu-ml/CRM
- **TRELLIS**: https://github.com/microsoft/TRELLIS
- **Zero123**: https://github.com/cvlab-columbia/zero123