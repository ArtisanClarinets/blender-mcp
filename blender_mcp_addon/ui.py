"""
UI panel for Blender MCP Addon

Provides the sidebar panel for controlling the addon.
"""

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty
from bpy.types import Panel, Operator, PropertyGroup

from . import server


class BlenderMCPSettings(PropertyGroup):
    """Settings for Blender MCP."""

    polyhaven_enabled: BoolProperty(
        name="Enable Poly Haven",
        description="Enable Poly Haven asset integration",
        default=True,
    )

    sketchfab_enabled: BoolProperty(
        name="Enable Sketchfab",
        description="Enable Sketchfab model integration",
        default=True,
    )

    hyper3d_enabled: BoolProperty(
        name="Enable Hyper3D",
        description="Enable Hyper3D Rodin AI generation",
        default=True,
    )

    hunyuan3d_enabled: BoolProperty(
        name="Enable Hunyuan3D",
        description="Enable Hunyuan3D AI generation",
        default=True,
    )

    telemetry_enabled: BoolProperty(
        name="Enable Telemetry",
        description="Enable anonymous usage tracking",
        default=True,
    )

    server_host: StringProperty(
        name="Host", description="Server host address", default="localhost"
    )

    server_port: IntProperty(
        name="Port", description="Server port number", default=9876, min=1024, max=65535
    )

    export_dir: StringProperty(
        name="Export Directory",
        description="Default directory for exports",
        default="//exports",
        subtype="DIR_PATH",
    )


class BLENDERMCP_OT_start_server(Operator):
    """Start the Blender MCP server."""

    bl_idname = "blendermcp.start_server"
    bl_label = "Start Server"
    bl_description = "Start the Blender MCP server"

    def execute(self, context):
        settings = context.scene.blendermcp_settings
        server.start_server(settings.server_host, settings.server_port)
        self.report({"INFO"}, "Server started")
        return {"FINISHED"}


class BLENDERMCP_OT_stop_server(Operator):
    """Stop the Blender MCP server."""

    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop Server"
    bl_description = "Stop the Blender MCP server"

    def execute(self, context):
        server.stop_server()
        self.report({"INFO"}, "Server stopped")
        return {"FINISHED"}


class BLENDERMCP_OT_test_connection(Operator):
    """Test the Blender MCP connection."""

    bl_idname = "blendermcp.test_connection"
    bl_label = "Test Connection"
    bl_description = "Test the connection to the MCP server"

    def execute(self, context):
        srv = server.get_server()
        if srv and srv.running:
            self.report({"INFO"}, "Server is running")
        else:
            self.report({"WARNING"}, "Server is not running")
        return {"FINISHED"}


class BLENDERMCP_PT_main_panel(Panel):
    """Main panel for Blender MCP."""

    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout

        # Safety check: ensure settings property is available
        if not hasattr(context.scene, "blendermcp_settings"):
            layout.label(text="Loading...", icon="INFO")
            return

        settings = context.scene.blendermcp_settings

        # Server status
        srv = server.get_server()
        if srv and srv.running:
            layout.label(text="Status: Running", icon="CHECKMARK")
            layout.operator("blendermcp.stop_server")
        else:
            layout.label(text="Status: Stopped", icon="X")
            layout.operator("blendermcp.start_server")

        layout.separator()

        # Connection test
        layout.operator("blendermcp.test_connection")

        layout.separator()

        # Settings
        box = layout.box()
        box.label(text="Settings:")
        box.prop(settings, "server_host")
        box.prop(settings, "server_port")

        layout.separator()

        # Integrations
        box = layout.box()
        box.label(text="Integrations:")
        box.prop(settings, "polyhaven_enabled")
        box.prop(settings, "sketchfab_enabled")
        box.prop(settings, "hyper3d_enabled")
        box.prop(settings, "hunyuan3d_enabled")

        layout.separator()

        # Export settings
        box = layout.box()
        box.label(text="Export:")
        box.prop(settings, "export_dir")

        layout.separator()

        # Telemetry
        box = layout.box()
        box.label(text="Privacy:")
        box.prop(settings, "telemetry_enabled")


classes = [
    BlenderMCPSettings,
    BLENDERMCP_OT_start_server,
    BLENDERMCP_OT_stop_server,
    BLENDERMCP_OT_test_connection,
    BLENDERMCP_PT_main_panel,
]


def register():
    """Register UI classes."""
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.blendermcp_settings = bpy.props.PointerProperty(
        type=BlenderMCPSettings
    )


def unregister():
    """Unregister UI classes."""
    del bpy.types.Scene.blendermcp_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
