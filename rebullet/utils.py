"""Utils imports"""

import shutil
import sys

from . import charDef as char
from . import colors

COLUMNS, _ = shutil.get_terminal_size()  ## Size of console


def handle_windows_input():
    import msvcrt

    # Flush the keyboard buffer
    while msvcrt.kbhit():
        msvcrt.getwch()
    if len(char.WIN_CH_BUFFER) != 0:
        return char.WIN_CH_BUFFER.pop(0)
    # Read the keystroke
    ch = msvcrt.getwch()
    encoding = "mbcs"
    # If it is a prefix char, get second part
    if ch.encode(encoding) in (b"\x00", b"\xe0"):
        ch = handle_prefix_char(ch, msvcrt, encoding)
    return ch


def handle_prefix_char(ch, msvcrt, encoding):
    ch2 = ch + msvcrt.getwch()
    # Translate actual Win chars to bullet char types
    try:
        chx = chr(char.WIN_CHAR_MAP[ch2.encode(encoding)])
        char.WIN_CH_BUFFER.append(chr(char.MOD_KEY_INT))
        char.WIN_CH_BUFFER.append(chx)
        if ord(chx) in (
            char.INSERT_KEY - char.MOD_KEY_FLAG,
            char.DELETE_KEY - char.MOD_KEY_FLAG,
            char.PG_UP_KEY - char.MOD_KEY_FLAG,
            char.PG_DOWN_KEY - char.MOD_KEY_FLAG,
        ):
            char.WIN_CH_BUFFER.append(chr(char.MOD_KEY_DUMMY))
        return chr(char.ESC_KEY)
    except KeyError:
        return ch2[1]


def handle_unix_input():
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)  # type: ignore
    try:
        tty.setraw(fd)  # type: ignore
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # type: ignore


def mygetc():
    """Get raw characters from input."""
    if sys.platform == "win32":
        return handle_windows_input()
    elif sys.platform in ("linux", "linux2", "darwin"):
        return handle_unix_input()


def getchar():
    """Character input parser."""
    c = mygetc()
    match ord(c):
        case char.LINE_BEGIN_KEY:
            return c
        case char.LINE_END_KEY:
            return c
        case char.TAB_KEY:
            return c
        case char.INTERRUPT_KEY:
            return c
        case char.NEWLINE_KEY:
            return c
        case char.BACK_SPACE_KEY:
            return c
        case char.BACK_SPACE_CHAR:
            return c

        case char.ESC_KEY:
            combo = mygetc()
            if ord(combo) != char.MOD_KEY_INT:
                return getchar()

            key = mygetc()
            if (
                ord(key) >= char.MOD_KEY_BEGIN - char.MOD_KEY_FLAG
                and ord(key) <= char.MOD_KEY_END - char.MOD_KEY_FLAG
            ):
                if ord(key) in (
                    char.HOME_KEY - char.MOD_KEY_FLAG,
                    char.END_KEY - char.MOD_KEY_FLAG,
                ):
                    return chr(ord(key) + char.MOD_KEY_FLAG)
                trail = mygetc()
                return (
                    chr(ord(key) + char.MOD_KEY_FLAG)
                    if ord(trail) == char.MOD_KEY_DUMMY
                    else chr(char.UNDEFINED_KEY)
                )
            elif (
                char.ARROW_KEY_BEGIN - char.ARROW_KEY_FLAG
                <= ord(key)
                <= char.ARROW_KEY_END - char.ARROW_KEY_FLAG
            ):
                return chr(ord(key) + char.ARROW_KEY_FLAG)
            else:
                return chr(char.UNDEFINED_KEY)
        case _:
            return c if is_printable(c) else chr(char.UNDEFINED_KEY)


# Basic command line functions


def move_cursor_left(n):
    """Move cursor left n columns."""
    force_write(f"\033[{n}D")


def move_cursor_right(n):
    """Move cursor right n columns."""
    force_write(f"\033[{n}C")


def move_cursor_up(n):
    """Move cursor up n rows."""
    force_write(f"\033[{n}A")


def move_cursor_down(n):
    """Move cursor down n rows."""
    force_write(f"\033[{n}B")


def move_cursor_head():
    """Move cursor to the start of line."""
    force_write("\r")


def clear_line():
    """Clear content of one line on the console."""
    force_write(" " * COLUMNS)
    move_cursor_head()


def clear_console_up(n):
    """Clear n console rows (bottom up)."""
    for _ in range(n):
        clear_line()
        move_cursor_up(1)


def clear_console_down(n):
    """Clear n console rows (top down)."""
    for _ in range(n):
        clear_line()
        move_cursor_down(1)
    move_cursor_up(n)


def force_write(s, end=""):
    """Dump everthing in the buffer to the console."""
    sys.stdout.write(s + end)
    sys.stdout.flush()


def cprint(
    s: str,
    color: str = colors.foreground["default"],
    on: str = colors.background["default"],
    end: str = "\n",
):
    """Colored print function.
    Args:
        s: The string to be printed.
        color: The color of the string.
        on: The color of the background.
        end: Last character appended.
    Returns:
        None
    """
    force_write(on + color + s + colors.RESET, end=end)


def is_printable(s: str) -> bool:
    """Determine if a string contains only printable characters.
    Args:
        s: The string to verify.
    Returns:
        bool: `True` if all characters in `s` are printable. `False` if any
            characters in `s` can not be printed.
    """
    # Ref: https://stackoverflow.com/a/50731077
    return not any(repr(ch).startswith(("'\\x", "'\\u")) for ch in s)
