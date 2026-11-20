"""Shared OBS websocket helpers."""
import os
import sys
import time

import obsws_python as obs

DEFAULT_SOURCE = "macOS Screen Capture"
HIDE_DELAY_SECONDS = 0.2  # hard-coded for now; OBS does not expose the hide transition duration


def connect() -> obs.ReqClient:
    return obs.ReqClient(
        host=os.environ.get("OBS_HOST", "localhost"),
        port=int(os.environ.get("OBS_PORT", "4455")),
        password=os.environ.get("OBS_PASSWORD", ""),
        timeout=5,
    )


WINDOW_MODE = 1  # screen_capture "type": 0 = display, 1 = window, 2 = application


def list_sources(client: obs.ReqClient) -> list[str]:
    """Names of macOS capture sources currently set to "Window" mode."""
    names = []
    for i in client.get_input_list().inputs:
        if i["inputKind"] != "screen_capture":
            continue
        settings = client.get_input_settings(i["inputName"]).input_settings
        if settings.get("type") == WINDOW_MODE:
            names.append(i["inputName"])
    return names


def list_windows(client: obs.ReqClient, source: str) -> list[dict]:
    """Windows OBS offers for the source, as [{"id": itemValue, "title": itemName}]."""
    items = client.get_input_properties_list_property_items(
        source, "window"
    ).property_items
    return [
        {"id": i["itemValue"], "title": i["itemName"]}
        for i in items
        if i.get("itemEnabled", True)
    ]


def get_current_window(client: obs.ReqClient, source: str):
    return client.get_input_settings(source).input_settings.get("window")


def set_window(client: obs.ReqClient, source: str, window_id) -> None:
    client.set_input_settings(source, {"window": window_id}, True)


def find_scene_item(client: obs.ReqClient, source: str) -> tuple[str, int]:
    """Locate the source's scene item (the thing the eye icon toggles) in the program scene."""
    scene = client.get_current_program_scene().scene_name
    item_id = client.get_scene_item_id(scene, source).scene_item_id
    return scene, item_id


def set_visible(client: obs.ReqClient, scene: str, item_id: int, visible: bool) -> None:
    """Equivalent to clicking the eye icon next to the source in OBS."""
    client.set_scene_item_enabled(scene, item_id, visible)


def switch_window(client: obs.ReqClient, source: str, window_id) -> None:
    """Hide the source, change its window, then show it again."""
    try:
        scene, item_id = find_scene_item(client, source)
    except Exception as e:
        print(f"Warning: could not find '{source}' in the current scene ({e}); "
              "changing window without hiding.", file=sys.stderr)
        set_window(client, source, window_id)
        return

    set_visible(client, scene, item_id, False)
    time.sleep(HIDE_DELAY_SECONDS)  # wait out the hide transition before re-showing
    try:
        set_window(client, source, window_id)
    finally:
        time.sleep(HIDE_DELAY_SECONDS)  # wait out the hide transition before re-showing
        set_visible(client, scene, item_id, True)


def scenes_top_to_bottom(client: obs.ReqClient) -> list[str]:
    """Scene names in the order of OBS's Scenes list, top first.

    OBS numbers scene indexes n (top) down to 0 (bottom), so sort by sceneIndex descending.
    """
    scenes = client.get_scene_list().scenes
    return [s["sceneName"] for s in sorted(scenes, key=lambda s: s["sceneIndex"], reverse=True)]


def scene_uses_source(client: obs.ReqClient, scene: str, source: str) -> bool:
    items = client.get_scene_item_list(scene).scene_items
    return any(i["sourceName"] == source for i in items)


def scene_to_leave_to(client: obs.ReqClient, source: str) -> str | None:
    """The scene closest to the top of the Scenes list that does not use the source."""
    for scene in scenes_top_to_bottom(client):
        if not scene_uses_source(client, scene, source):
            return scene
    return None


def scene_to_enter(client: obs.ReqClient, source: str, current: str) -> str | None:
    """First scene using the source, going down the Scenes list from the current scene.

    Wraps back to the top if nothing below the current scene uses the source.
    """
    scenes = scenes_top_to_bottom(client)
    start = scenes.index(current) if current in scenes else 0
    for scene in scenes[start:] + scenes[:start]:
        if scene_uses_source(client, scene, source):
            return scene
    return None


def current_scene(client: obs.ReqClient) -> str:
    return client.get_current_program_scene().scene_name


def set_scene(client: obs.ReqClient, name: str) -> None:
    client.set_current_program_scene(name)
