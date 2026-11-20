"""Pure helpers for filtering, sorting and labeling the windows OBS reports (no Qt)."""

OWN_TITLE = "OBS Window Selector"
HIDDEN_OWNERS = ("[Control Center]", "[Notification Center]")


def is_filtered(title: str) -> bool:
    """True for windows hidden unless "Show all" is on."""
    return (
        not title.strip()
        or title.startswith(HIDDEN_OWNERS)
        or title.endswith(OWN_TITLE)
    )


def owner(title: str) -> str:
    """The "[Owner]" prefix text of a window title, or the whole title if it has none."""
    if title.startswith("[") and "]" in title:
        return title[1 : title.index("]")]
    return title


def sort_key(w: dict) -> tuple:
    """Group by app (alphabetical), then window ID ascending."""
    wid = w["id"] if isinstance(w["id"], int) else 0
    return (owner(w["title"]).casefold(), wid, w["title"])


def window_title(title: str) -> str:
    """The title without its "[Owner]" prefix."""
    _owner, sep, rest = title.partition("] ")
    return rest if title.startswith("[") and sep else title
