---
id: 003
title: Auto Switch
status: implemented
---

The scenes list in OBS orders scene indexes from n(top)-0(bottom)

1. Add a checkbox, "Auto scene switch", on the same line as the current toggle button,
but left-aligned. When checked, watch the list of windows to see if the currently selected
window is removed from the list.

If window is removed from the list:
- Changes to an empty window and the current active scene in OBS was using that source: Start a 300ms countdown. Cancel the countdown if the value
of the window is updated to a non-empty value. If the countdown does not get cancelled,
switch the scene to the scene closest to the top of the Scenes list that is not using that source.

If a source item in the list is clicked while not viewing a scene that is using 
the configured Source:
- Switch to the first scene, starting from the index of the current active scene,
going down the list, that is using the configured source.

2. Click an already selected item in the list will unselect it and set the Source
Window to the "blank" entry.