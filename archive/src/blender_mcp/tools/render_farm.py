
"""
Render farm integration and distributed rendering

Provides tools for managing large-scale rendering operations.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from ..mcp_compat import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("create_render_job")
@mcp.tool()
async def create_render_job(
    ctx: Context,
    job_name: str,
    frame_range: List[int],
    output_path: str,
    priority: int = 1,
    nodes: int = 1,
    render_settings: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a render farm job.
    
    Parameters:
    - job_name: Name of the render job
    - frame_range: [start, end] frame range
    - output_path: Output directory
    - priority: Job priority (1-10)
    - nodes: Number of render nodes
    - render_settings: Additional render settings
    
    Returns:
    - JSON string with job creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "job_name": job_name,
            "frame_range": frame_range,
            "output_path": output_path,
            "priority": priority,
            "nodes": nodes,
        }
        
        if render_settings:
            params["render_settings"] = render_settings
            
        result = blender.send_command("create_render_job", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating render job: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("monitor_render_job")
@mcp.tool()
async def monitor_render_job(
    ctx: Context,
    job_id: str,
) -> str:
    """
    Monitor render job progress.
    
    Parameters:
    - job_id: Render job ID
    
    Returns:
    - JSON string with job status
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "job_id": job_id,
        }
        
        result = blender.send_command("monitor_render_job", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error monitoring render job: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("optimize_render_settings")
@mcp.tool()
async def optimize_render_settings(
    ctx: Context,
    quality_target: str = "production",
    time_budget: Optional[float] = None,
    memory_limit: Optional[float] = None,
) -> str:
    """
    Optimize render settings for quality/time balance.
    
    Parameters:
    - quality_target: Target quality ("preview", "draft", "production")
    - time_budget: Time budget per frame (seconds)
    - memory_limit: Memory limit (GB)
    
    Returns:
    - JSON string with optimized settings
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "quality_target": quality_target,
        }
        
        if time_budget:
            params["time_budget"] = time_budget
        if memory_limit:
            params["memory_limit"] = memory_limit
            
        result = blender.send_command("optimize_render_settings", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error optimizing render settings: {str(e)}")
        return json.dumps({"error": str(e)})
