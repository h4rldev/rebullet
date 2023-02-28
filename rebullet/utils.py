"""Utils imports"""
import shutil
import sys

from . import charDef as char
from . import colors

COLUMNS, _ = shutil.get_terminal_size()  ## Size of console


def mygetc():
    """Get raw characters from input."""
    if sys.platform == "win32":
        import msvcrt

        encoding = "mbcs"
        # Flush the keyboard buffer
        while msvcrt.kbhit():
            msvcrt.getwch()
        if len(char.WIN_CH_BUFFER) == 0:
            # Read the keystroke
            ch = msvcrt.getwch()
            # If it is a prefix char, get second part
            if ch.encode(encoding) in (b"\x00", b"\xe0"):
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
                    ch = chr(char.ESC_KEY)
                except KeyError:
                    ch = ch2[1]
            else:
                pass
        else:
            ch = char.WIN_CH_BUFFER.pop(0)
    elif sys.platform in ("linux", "linux2", "darwin"):
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


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
            if ord(combo) == char.MOD_KEY_INT:
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
                    else:
                        trail = mygetc()
                        if ord(trail) == char.MOD_KEY_DUMMY:
                            return chr(ord(key) + char.MOD_KEY_FLAG)
                        else:
                            return char.UNDEFINED_KEY
                elif (
                    char.ARROW_KEY_BEGIN - char.ARROW_KEY_FLAG
                    <= ord(key)
                    <= char.ARROW_KEY_END - char.ARROW_KEY_FLAG
                ):
                    return chr(ord(key) + char.ARROW_KEY_FLAG)
                else:
                    return char.UNDEFINED_KEY
            else:
                return getchar()

        case _:
            if is_printable(c):
                return c
            else:
                return char.UNDEFINED_KEY

    return char.UNDEFINED_KEY


# Basic command line functions


def moveCursorLeft(n):
    """Move cursor left n columns."""
    forceWrite("\033[{}D".format(n))


def moveCursorRight(n):
    """Move cursor right n columns."""
    forceWrite("\033[{}C".format(n))


def moveCursorUp(n):
    """Move cursor up n rows."""
    forceWrite("\033[{}A".format(n))


def moveCursorDown(n):
    """Move cursor down n rows."""
    forceWrite("\033[{}B".format(n))


def moveCursorHead():
    """Move cursor to the start of line."""
    forceWrite("\r")


def clearLine():
    """Clear content of one line on the console."""
    forceWrite(" " * COLUMNS)
    moveCursorHead()


def clearConsoleUp(n):
    """Clear n console rows (bottom up)."""
    for _ in range(n):
        clearLine()
        moveCursorUp(1)


def clearConsoleDown(n):
    """Clear n console rows (top down)."""
    for _ in range(n):
        clearLine()
        moveCursorDown(1)
    moveCursorUp(n)


def forceWrite(s, end=""):
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
    forceWrite(on + color + s + colors.RESET, end=end)


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
