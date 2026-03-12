
"""
Atmospheric effects and environmental systems

Provides tools for creating realistic atmospheric conditions and weather effects.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("create_volumetric_fog")
@mcp.tool()
async def create_volumetric_fog(
    ctx: Context,
    density: float = 0.1,
    height: float = 10.0,
    falloff: float = 1.0,
    color: Optional[List[float]] = None,
    noise_scale: float = 1.0,
) -> str:
    """
    Create volumetric fog effect.
    
    Parameters:
    - density: Fog density
    - height: Fog height
    - falloff: Height falloff
    - color: Fog color
    - noise_scale: Noise scale for variation
    
    Returns:
    - JSON string with fog creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "density": density,
            "height": height,
            "falloff": falloff,
            "noise_scale": noise_scale,
        }
        
        if color:
            params["color"] = color
            
        result = blender.send_command("create_volumetric_fog", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating volumetric fog: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_weather_system")
@mcp.tool()
async def create_weather_system(
    ctx: Context,
    weather_type: str,
    intensity: float = 0.5,
    coverage: float = 0.5,
    wind_speed: float = 0.0,
    wind_direction: Optional[List[float]] = None,
) -> str:
    """
    Create a weather system with particles and effects.
    
    Parameters:
    - weather_type: Type of weather ("rain", "snow", "dust", "leaves")
    - intensity: Weather intensity
    - coverage: Area coverage
    - wind_speed: Wind speed
    - wind_direction: Wind direction vector
    
    Returns:
    - JSON string with weather system creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "weather_type": weather_type,
            "intensity": intensity,
            "coverage": coverage,
            "wind_speed": wind_speed,
        }
        
        if wind_direction:
            params["wind_direction"] = wind_direction
            
        result = blender.send_command("create_weather_system", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating weather system: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_sky_system")
@mcp.tool()
async def create_sky_system(
    ctx: Context,
    sky_type: str = "nishita",
    time_of_day: float = 12.0,
    turbidity: float = 2.0,
    rayleigh: float = 2.0,
    mie: float = 0.005,
) -> str:
    """
    Create a physically accurate sky system.
    
    Parameters:
    - sky_type: Sky model ("nishita", "preetham", "hosek_wilkie")
    - time_of_day: Time of day (0-24)
    - turbidity: Atmospheric turbidity
    - rayleigh: Rayleigh scattering
    - mie: Mie scattering
    
    Returns:
    - JSON string with sky system creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "sky_type": sky_type,
            "time_of_day": time_of_day,
            "turbidity": turbidity,
            "rayleigh": rayleigh,
            "mie": mie,
        }
        
        result = blender.send_command("create_sky_system", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating sky system: {str(e)}")
        return json.dumps({"error": str(e)})
