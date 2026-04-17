"""MCP request handlers for Blender operations."""

import bpy
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_scene_info() -> dict:
    """Return basic info about the current Blender scene."""
    scene = bpy.context.scene
    objects = [
        {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "visible": obj.visible_get(),
        }
        for obj in scene.objects
    ]
    return {
        "name": scene.name,
        "frame_current": scene.frame_current,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "object_count": len(objects),
        "objects": objects,
    }


def create_object(obj_type: str, name: str = None, location: list = None) -> dict:
    """Create a new mesh primitive in the scene."""
    loc = location or [0.0, 0.0, 0.0]
    type_map = {
        "cube": bpy.ops.mesh.primitive_cube_add,
        "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
        "cylinder": bpy.ops.mesh.primitive_cylinder_add,
        "plane": bpy.ops.mesh.primitive_plane_add,
        "cone": bpy.ops.mesh.primitive_cone_add,
        "torus": bpy.ops.mesh.primitive_torus_add,
    }
    op = type_map.get(obj_type.lower())
    if op is None:
        raise ValueError(f"Unknown object type: {obj_type}. Choose from {list(type_map.keys())}")

    op(location=loc)
    obj = bpy.context.active_object
    if name:
        obj.name = name
    return {"name": obj.name, "type": obj.type, "location": list(obj.location)}


def delete_object(name: str) -> dict:
    """Delete an object by name from the scene."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Object '{name}' not found in scene")
    bpy.data.objects.remove(obj, do_unlink=True)
    return {"deleted": name}


def set_object_location(name: str, location: list) -> dict:
    """Move an object to the given world-space location."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Object '{name}' not found in scene")
    obj.location = location
    return {"name": obj.name, "location": list(obj.location)}


def execute_python(code: str) -> dict:
    """Execute arbitrary Python code in Blender's context. Use with caution."""
    local_ns: dict[str, Any] = {}
    try:
        exec(code, {"bpy": bpy}, local_ns)  # noqa: S102
        return {"status": "ok", "result": str(local_ns.get("result", ""))}
    except Exception as exc:
        logger.exception("execute_python failed")
        return {"status": "error", "error": str(exc)}


DISPATCH: dict[str, Any] = {
    "get_scene_info": get_scene_info,
    "create_object": create_object,
    "delete_object": delete_object,
    "set_object_location": set_object_location,
    "execute_python": execute_python,
}


def handle_request(raw: str) -> str:
    """Parse a JSON request and dispatch to the appropriate handler.

    Expected request format::

        {"action": "create_object", "params": {"obj_type": "cube"}}

    Returns a JSON-encoded response string.
    """
    try:
        request = json.loads(raw)
        action = request.get("action")
        params = request.get("params", {})
        if action not in DISPATCH:
            return json.dumps({"error": f"Unknown action: {action}"})
        result = DISPATCH[action](**params)
        return json.dumps({"result": result})
    except (ValueError, TypeError) as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("Unhandled error in handle_request")
        return json.dumps({"error": f"Internal error: {exc}"})
