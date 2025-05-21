"""Color Codes."""

foreground = {
    "black": "\u001b[30m",
    "red": "\u001b[31m",
    "green": "\u001b[32m",
    "yellow": "\u001b[33m",
    "blue": "\u001b[34m",
    "magenta": "\u001b[35m",
    "cyan": "\u001b[36m",
    "white": "\u001b[37m",
    "default": "\u001b[39m",
}

background = {
    "black": "\u001b[40m",
    "red": "\u001b[41m",
    "green": "\u001b[42m",
    "yellow": "\u001b[43m",
    "blue": "\u001b[44m",
    "magenta": "\u001b[45m",
    "cyan": "\u001b[46m",
    "white": "\u001b[47m",
    "default": "\u001b[49m",
}

REVERSE = "\u001b[7m"
RESET_REVERSE = "\u001b[27m"

RESET = "\u001b[0m"


def bright(color, mapping=None):
    """Return the bright version of a color.
    Accepts either a color name or an ANSI code.
    Optionally, provide a mapping (e.g., foreground or background).
    """
    # If mapping is provided and color is a name, resolve it
    if mapping and isinstance(color, str) and color in mapping:
        color = mapping[color]
    # If color is a known color name, try foreground and background
    elif isinstance(color, str) and color in foreground:
        color = foreground[color]
    elif isinstance(color, str) and color in background:
        color = background[color]
    # Now color should be an ANSI code string
    if isinstance(color, str) and color.startswith("\u001b["):
        # Replace 'm' at the end with ';1m' for bright
        if color.endswith("m"):
            return color[:-1] + ";1m"
    return color  # fallback: return as is
