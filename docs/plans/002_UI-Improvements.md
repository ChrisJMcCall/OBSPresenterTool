---
id: 002
title: UI Improvements
status: implemented
---

# UI Improvements

Work through these tasks in sequence, one at a time. When one task is complete, ask if I would like
to move on to the next.

1. ~~When the application starts up, prompt for a password instead of using an environment variable.
   Store this password so that it is not necessary to reenter it on every start.~~

2. Use a drop-down list to select the OBS source instead of a hard-coded value. Save the last used
   selection and automatically select it on the next start.

3. Filter out windows from the list: [Control Center], [Notification Center], and the application's
   own window. Add a "Show all" toggle button above the list to disable the filter.

4. Add a line break after the "[OwnerName]" so that the list is more readable. Add a seperator
   between list items.

5. Remove whatever is causing the window to hide when it loses focus.

6. When scrolling with the mouse wheel, the list moves in increments. Make the list scroll smoothly.

7. After selecting a new window from the list, the scroll position changes after a pause. Prevent
   the list scroll position from changing.

8. When the application starts up, adjust the scroll position of the list so that the selected item
   is visible.

9. Get the application icon for each Owner and replace "[OwnerName]" with the icon. Remove the
   window ID from the list, but keep the ordering. Position the app icon so that it is aligned to
   the top-left of the list item and not vertically centered.

10. Change the color of the list item seperator to a light grey.

11. Only show the drop-down if there is more than one source set to "Window" mode. If there is only
    one source that is set to window mode, select it, and hide the drop down.

12. Add 10px top and bottom padding to the items in the window list. Change the text of the window
    titles to not wrap. Truncate the text with "..." if it is too long to fit in the list without
    wrapping. Allow the full title to be shown as a tooltip when hovering. The title should be
    vertically centered in the list item.
