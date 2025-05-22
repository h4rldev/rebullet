"""Client imports."""

import re
from collections import defaultdict
from datetime import date

from dateutil import parser as date_parser

from . import charDef as char
from . import colors, cursor, keyhandler, utils
from .exceptions import MissingDependenciesError
from .wrap_text import wrap_text


# Reusable private utility class
class myInput:
    """
    Custom input handler for interactive CLI input with color and password support.

    Args:
        word_color (str): Foreground color for input text. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        password (bool): If True, input is masked (for passwords).
        hidden (str): Character to display for masked input.
    """

    def __init__(
        self,
        word_color: str = colors.foreground["default"],
        password: bool = False,
        hidden: str = "*",
    ):
        self.buffer = []  # Buffer to store entered characters
        self.pos = 0  # Current cursor position
        self.password = password
        self.hidden = hidden
        self.word_color = word_color

    def moveCursor(self, pos):
        """Move cursort to pos in buffer."""
        if pos < 0 or pos > len(self.buffer):
            return False
        if self.pos <= pos:
            while self.pos != pos:
                if self.password:
                    utils.cprint(self.hidden, color=self.word_color, end="")
                else:
                    utils.cprint(self.buffer[self.pos], color=self.word_color, end="")
                self.pos += 1
        else:
            while self.pos != pos:
                utils.forceWrite("\b")
                self.pos -= 1
        return True

    def insertChar(self, c):
        """Insert character c to buffer at current position."""
        self.buffer.insert(self.pos, c)
        if self.password:
            utils.cprint(
                self.hidden * (len(self.buffer) - self.pos),
                color=self.word_color,
                end="",
            )
        else:
            utils.cprint(
                "".join(self.buffer[self.pos :]), color=self.word_color, end=""
            )
        utils.forceWrite("\b" * (len(self.buffer) - self.pos - 1))
        self.pos += 1

    def getInput(self):
        """Return content in buffer."""
        ret = "".join(self.buffer)
        self.buffer = []
        self.pos = 0
        return ret

    def deleteChar(self):
        """Remove character at current cursor position."""
        if self.pos == len(self.buffer):
            return
        self.buffer.pop(self.pos)
        if self.hidden:
            utils.forceWrite(self.hidden * (len(self.buffer) - self.pos) + " ")
        else:
            utils.forceWrite("".join(self.buffer[self.pos :]) + " ")
        utils.forceWrite("\b" * (len(self.buffer) - self.pos + 1))

    def input(self):
        while True:
            c = utils.getchar()
            i = c if c == char.UNDEFINED_KEY else ord(c)

            match i:
                case char.NEWLINE_KEY:
                    utils.forceWrite("\n")
                    return self.getInput()
                case char.LINE_BEGIN_KEY:
                    return
                case char.HOME_KEY:
                    return
                case char.LINE_END_KEY:
                    return
                case char.END_KEY:
                    return
                case char.ARROW_UP_KEY:
                    return
                case char.ARROW_DOWN_KEY:
                    return
                case char.PG_UP_KEY:
                    return
                case char.PG_DOWN_KEY:
                    return
                case char.TAB_KEY:
                    return
                case char.UNDEFINED_KEY:
                    return
                case char.BACK_SPACE_KEY:
                    if self.moveCursor(self.pos - 1):
                        self.deleteChar()
                case char.BACK_SPACE_CHAR:
                    if self.moveCursor(self.pos - 1):
                        self.deleteChar()
                case char.DELETE_KEY:
                    self.deleteChar()
                case char.ARROW_RIGHT_KEY:
                    self.moveCursor(self.pos + 1)
                case char.ARROW_LEFT_KEY:
                    self.moveCursor(self.pos - 1)
                case _:
                    if self.password:
                        if c != " ":
                            self.insertChar(c)
                    else:
                        self.insertChar(c)


@keyhandler.init
class Bullet:
    """
    Interactive bullet list selector for CLI with color customization.

    Args:
        prompt (str): Prompt text.
        choices (list): List of choices to display.
        bullet (str): Bullet character.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        bullet_color (str): Foreground color for bullet. Available: same as above.
        word_color (str): Foreground color for choices. Available: same as above.
        word_on_switch (str): Foreground color for selected choice. Available: same as above, or use colors.REVERSE for reverse video.
        background_color (str): Background color for choices. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        background_on_switch (str): Background color for selected choice. Available: same as above, or use colors.REVERSE.
        pad_right (int): Padding to the right of choices.
        indent (int): Indentation from left.
        align (int): Additional alignment spaces.
        margin (int): Margin between bullet and text.
        shift (int): Lines to shift down after prompt.
        return_index (bool): If True, return (choice, index).
    """

    def __init__(
        self,
        prompt: str = "",
        choices: list = None,
        bullet: str = "●",
        prompt_color: str = colors.foreground["default"],
        bullet_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
        word_on_switch: str = colors.REVERSE,
        background_color: str = colors.background["default"],
        background_on_switch: str = colors.REVERSE,
        pad_right=0,
        indent: int = 0,
        align=0,
        margin: int = 0,
        shift: int = 0,
        return_index: bool = False,
    ):
        if not choices:
            raise ValueError("Choices can not be empty!")
        if indent < 0:
            raise ValueError("Indent must be > 0!")
        if margin < 0:
            raise ValueError("Margin must be > 0!")

        self.prompt = prompt
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        self.choices = choices
        self.pos = 0

        self.indent = indent
        self.align = align
        self.margin = margin
        self.shift = shift

        self.bullet = bullet
        self.bullet_color         = utils.resolve_color(bullet_color, colors.foreground)
        self.word_color           = utils.resolve_color(word_color, colors.foreground)
        self.word_on_switch       = utils.resolve_color(word_on_switch, colors.foreground)
        self.background_color     = utils.resolve_color(background_color, colors.background)
        self.background_on_switch = utils.resolve_color(background_on_switch, colors.background)
        self.pad_right = pad_right

        self.max_width = len(max(self.choices, key=len)) + self.pad_right
        self.return_index = return_index

    def renderBullets(self):
        for i in range(len(self.choices)):
            self.printBullet(i)
            utils.forceWrite("\n")

    def printBullet(self, idx):
        utils.forceWrite(" " * (self.indent + self.align))
        back_color = (
            self.background_on_switch if idx == self.pos else self.background_color
        )
        word_color = self.word_on_switch if idx == self.pos else self.word_color
        if idx == self.pos:
            utils.cprint(
                "{}".format(self.bullet) + " " * self.margin,
                self.bullet_color,
                back_color,
                end="",
            )
        else:
            utils.cprint(
                " " * (len(self.bullet) + self.margin),
                self.bullet_color,
                back_color,
                end="",
            )
        utils.cprint(self.choices[idx], word_color, back_color, end="")
        utils.cprint(
            " " * (self.max_width - len(self.choices[idx])), on=back_color, end=""
        )
        utils.moveCursorHead()

    @keyhandler.register(char.ARROW_UP_KEY)
    def moveUp(self):
        if self.pos - 1 < 0:
            return
        else:
            utils.clearLine()
            old_pos = self.pos
            self.pos -= 1
            self.printBullet(old_pos)
            utils.moveCursorUp(1)
            self.printBullet(self.pos)

    @keyhandler.register(char.ARROW_DOWN_KEY)
    def moveDown(self):
        if self.pos + 1 >= len(self.choices):
            return
        else:
            utils.clearLine()
            old_pos = self.pos
            self.pos += 1
            self.printBullet(old_pos)
            utils.moveCursorDown(1)
            self.printBullet(self.pos)

    @keyhandler.register(char.HOME_KEY)
    def moveTop(self):
        utils.clearLine()
        old_pos = self.pos
        self.pos = 0
        self.printBullet(old_pos)
        while old_pos > 0:
            utils.moveCursorUp(1)
            old_pos -= 1
        self.printBullet(self.pos)

    @keyhandler.register(char.END_KEY)
    def moveBottom(self):
        utils.clearLine()
        old_pos = self.pos
        self.pos = len(self.choices) - 1
        self.printBullet(old_pos)
        while old_pos < len(self.choices) - 1:
            utils.moveCursorDown(1)
            old_pos += 1
        self.printBullet(self.pos)

    @keyhandler.register(char.NEWLINE_KEY)
    def accept(self):
        utils.moveCursorDown(len(self.choices) - self.pos)
        ret = self.choices[self.pos]
        if self.return_index:
            return ret, self.pos
        self.pos = 0
        return ret

    @keyhandler.register(char.INTERRUPT_KEY)
    def interrupt(self):
        utils.moveCursorDown(len(self.choices) - self.pos)
        raise KeyboardInterrupt

    def launch(self, default=None):
        if self.prompt:
            utils.forceWrite(
                " " * self.indent
                + self.prompt_color
                + self.prompt
                + colors.RESET
                + "\n"
            )
            utils.forceWrite("\n" * self.shift)
        if default is not None:
            if type(default).__name__ != "int":
                raise TypeError("'default' should be an integer value!")
            if not 0 <= int(default) < len(self.choices):
                raise ValueError("'default' should be in range [0, len(choices))!")
            self.pos = default
        self.renderBullets()
        utils.moveCursorUp(len(self.choices) - self.pos)
        with cursor.hide():
            while True:
                ret = self.handle_input()
                if ret is not None:
                    return ret


@keyhandler.init
class Check:
    """
    Interactive checkbox list selector for CLI with color customization.

    Args:
        prompt (str): Prompt text.
        choices (list): List of choices to display.
        check (str): Checkmark character.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        check_color (str): Foreground color for checkmark. Available: same as above.
        check_on_switch (str): Foreground color for selected checkmark. Available: same as above, or colors.REVERSE.
        word_color (str): Foreground color for choices. Available: same as above.
        word_on_switch (str): Foreground color for selected choice. Available: same as above, or colors.REVERSE.
        background_color (str): Background color for choices. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        background_on_switch (str): Background color for selected choice. Available: same as above, or colors.REVERSE.
        pad_right (int): Padding to the right of choices.
        indent (int): Indentation from left.
        align (int): Additional alignment spaces.
        margin (int): Margin between check and text.
        shift (int): Lines to shift down after prompt.
        return_index (bool): If True, return (choices, indices).
    """

    def __init__(
        self,
        prompt: str = "",
        choices: list = None,
        check: str = "√",
        prompt_color: str = colors.foreground["default"],
        check_color: str = colors.foreground["default"],
        check_on_switch: str = colors.REVERSE,
        word_color: str = colors.foreground["default"],
        word_on_switch: str = colors.REVERSE,
        background_color: str = colors.background["default"],
        background_on_switch: str = colors.REVERSE,
        pad_right=0,
        indent: int = 0,
        align=0,
        margin: int = 0,
        shift: int = 0,
        return_index: bool = False,
    ):
        if not choices:
            raise ValueError("Choices can not be empty!")
        if indent < 0:
            raise ValueError("Indent must be > 0!")
        if margin < 0:
            raise ValueError("Margin must be > 0!")

        self.prompt = prompt
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        self.choices = choices
        self.checked = [False] * len(self.choices)
        self.pos = 0

        self.indent = indent
        self.align = align
        self.margin = margin
        self.shift = shift

        self.check = check
        self.check_color = utils.resolve_color(check_color, colors.foreground)
        self.check_on_switch = utils.resolve_color(check_on_switch, colors.foreground)

        self.word_color = utils.resolve_color(word_color, colors.foreground)
        self.word_on_switch = utils.resolve_color(word_on_switch, colors.foreground)
        self.background_color = utils.resolve_color(background_color, colors.background)
        self.background_on_switch = utils.resolve_color(background_on_switch, colors.background)
        self.pad_right = pad_right

        self.max_width = len(max(self.choices, key=len)) + self.pad_right
        self.return_index = return_index

    def renderRows(self):
        for i in range(len(self.choices)):
            self.printRow(i)
            utils.forceWrite("\n")

    def printRow(self, idx):
        utils.forceWrite(" " * (self.indent + self.align))
        back_color = (
            self.background_on_switch if idx == self.pos else self.background_color
        )
        word_color = self.word_on_switch if idx == self.pos else self.word_color
        check_color = self.check_on_switch if idx == self.pos else self.check_color
        if self.checked[idx]:
            utils.cprint(
                "{}".format(self.check) + " " * self.margin,
                check_color,
                back_color,
                end="",
            )
        else:
            utils.cprint(
                " " * (len(self.check) + self.margin), check_color, back_color, end=""
            )
        utils.cprint(self.choices[idx], word_color, back_color, end="")
        utils.cprint(
            " " * (self.max_width - len(self.choices[idx])), on=back_color, end=""
        )
        utils.moveCursorHead()

    @keyhandler.register(char.SPACE_CHAR)
    def toggleRow(self):
        self.checked[self.pos] = not self.checked[self.pos]
        self.printRow(self.pos)

    @keyhandler.register(char.ARROW_UP_KEY)
    def moveUp(self):
        if self.pos - 1 < 0:
            return
        else:
            utils.clearLine()
            old_pos = self.pos
            self.pos -= 1
            self.printRow(old_pos)
            utils.moveCursorUp(1)
            self.printRow(self.pos)

    @keyhandler.register(char.ARROW_DOWN_KEY)
    def moveDown(self):
        if self.pos + 1 >= len(self.choices):
            return
        else:
            utils.clearLine()
            old_pos = self.pos
            self.pos += 1
            self.printRow(old_pos)
            utils.moveCursorDown(1)
            self.printRow(self.pos)

    @keyhandler.register(char.HOME_KEY)
    def moveTop(self):
        utils.clearLine()
        old_pos = self.pos
        self.pos = 0
        self.printRow(old_pos)
        while old_pos > 0:
            utils.moveCursorUp(1)
            old_pos -= 1
        self.printRow(self.pos)

    @keyhandler.register(char.END_KEY)
    def moveBottom(self):
        utils.clearLine()
        old_pos = self.pos
        self.pos = len(self.choices) - 1
        self.printRow(old_pos)
        while old_pos < len(self.choices) - 1:
            utils.moveCursorDown(1)
            old_pos += 1
        self.printRow(self.pos)

    @keyhandler.register(char.NEWLINE_KEY)
    def accept(self):
        utils.moveCursorDown(len(self.choices) - self.pos)
        ret = [self.choices[i] for i in range(len(self.choices)) if self.checked[i]]
        ret_idx = [i for i in range(len(self.choices)) if self.checked[i]]
        self.pos = 0
        self.checked = [False] * len(self.choices)
        if self.return_index:
            return ret, ret_idx
        return ret

    @keyhandler.register(char.INTERRUPT_KEY)
    def interrupt(self):
        utils.moveCursorDown(len(self.choices) - self.pos)
        raise KeyboardInterrupt

    def launch(self, default=None):
        if self.prompt:
            utils.forceWrite(
                " " * self.indent
                + self.prompt_color
                + self.prompt
                + colors.RESET
                + "\n"
            )
            utils.forceWrite("\n" * self.shift)
        if default is None:
            default = []
        if default:
            if not type(default).__name__ == "list":
                raise TypeError("`default` should be a list of integers!")
            if not all([type(i).__name__ == "int" for i in default]):
                raise TypeError("Indices in `default` should be integer type!")
            if not all([0 <= i < len(self.choices) for i in default]):
                raise ValueError(
                    "All indices in `default` should be in range [0, len(choices))!"
                )
            for i in default:
                self.checked[i] = True
        self.renderRows()
        utils.moveCursorUp(len(self.choices))
        with cursor.hide():
            while True:
                ret = self.handle_input()
                if ret is not None:
                    return ret


class CheckDependencies(Check):
    """
    Checkbox selector with dependency management between choices.

    Args:
        prompt (str): Prompt text.
        dep_tree (tuple): Tuple of (choice, dependencies) pairs.
        All color arguments as in Check.
    """

    def __init__(self, prompt="", dep_tree=(), *args, **kwargs):
        """Extract choices from the dep_tree."""
        """
        dep_tree expected format:
        (
            ("choice A", ("choice C", "Choice D")),
            ("choice B", ("choice A", "Choice E")),
            ("choice C", ()),
            ("choice D", ("choice C",)),
            ("choice E", ("choice B",)),
        #    ^choices^    ^dependencies list^
        )
        """
        self.validateDependencies(dep_tree)
        self.dependencies = {k: v for k, v in dep_tree}
        self.dependants = defaultdict(set)
        for k, deps in dep_tree:
            for d in deps:
                self.dependants[d].add(k)
        choices = [c[0] for c in dep_tree]
        # trunk-ignore(ruff/B026)
        super().__init__(prompt=prompt, choices=choices, *args, **kwargs)

    def validateDependencies(self, dep_tree):
        missing_dependencies = []
        items = [item for item, dependencies in dep_tree]
        for item, dependencies in dep_tree:
            for dep in dependencies:
                if dep not in items:
                    missing_dependencies.append((item, dep))
        if missing_dependencies:
            raise MissingDependenciesError(missing_dependencies)

    @keyhandler.register(char.SPACE_CHAR)
    def toggleRow(self):
        super().toggleRow()
        if self.checked[self.pos]:
            self.checkDependencies(self.choices[self.pos])
        else:
            self.uncheckDependants(self.choices[self.pos])
        self.refresh()

    def checkDependencies(self, choice, checks=None):
        checks = checks or [choice]
        deps = self.dependencies[choice]
        for dep in deps:
            if self.checked[self.choices.index(dep)] not in checks:
                self.checked[self.choices.index(dep)] = True
                checks.append(self.checked[self.choices.index(dep)])
                self.checkDependencies(dep, checks)

    def uncheckDependants(self, choice, unchecks=None):
        unchecks = unchecks or [choice]
        deps = self.dependants[choice]
        for dep in deps:
            if self.checked[self.choices.index(dep)] not in unchecks:
                self.checked[self.choices.index(dep)] = False
                unchecks.append(self.checked[self.choices.index(dep)])
                self.uncheckDependants(dep, unchecks)

    def refresh(self):
        if not self.pos == 0:
            utils.moveCursorUp(self.pos)
        utils.clearLine()
        self.printRow(0)
        for pos in range(1, len(self.choices)):
            utils.moveCursorDown(0)
            utils.clearLine()
            self.printRow(pos)
        if not self.pos == len(self.choices) - 1:
            utils.moveCursorUp(len(self.choices) - self.pos - 1)


class YesNo:
    """
    Yes/No prompt for CLI with color customization.

    Args:
        prompt (str): Prompt text.
        default (str): Default answer ('y' or 'n').
        indent (int): Indentation from left.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        word_color (str): Foreground color for user input. Available: same as above.
        prompt_prefix (str): Prefix for prompt (e.g., '[y/n] ').
    """

    def __init__(
        self,
        prompt: str = "",
        default: str = "y",
        indent: int = 0,
        prompt_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
        prompt_prefix: str = "[y/n] ",
    ):
        self.indent = indent
        if not prompt:
            raise ValueError("Prompt can not be empty!")
        if default.lower() not in ["y", "n"]:
            raise ValueError("`default` can only be 'y' or 'n'!")
        self.default = f"[{default.lower()}]: "
        self.prompt = prompt_prefix + prompt
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        self.word_color = utils.resolve_color(word_color, colors.foreground)

    def valid(self, ans):
        if ans is None:
            return False
        ans = ans.lower()
        if "yes".startswith(ans) or "no".startswith(ans):
            return True
        utils.moveCursorUp(self.prompt.count("\n") + 1)
        utils.forceWrite(
            " " * self.indent
            + self.prompt_color
            + self.prompt
            + self.default
            + colors.RESET
        )
        utils.forceWrite(" " * len(ans))
        utils.forceWrite("\b" * len(ans))
        return False

    def launch(self):
        my_input = myInput(word_color=self.word_color)
        utils.forceWrite(
            " " * self.indent
            + self.prompt_color
            + self.prompt
            + self.default
            + colors.RESET
        )
        while True:
            ans = my_input.input()
            if ans == "":
                return self.default.strip("[]: ") == "y"
            if not self.valid(ans):
                continue
            else:
                return "yes".startswith(ans.lower())


class Input:
    """
    Text input prompt for CLI with color and pattern validation.

    Args:
        prompt (str): Prompt text.
        default (str): Default value.
        indent (int): Indentation from left.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        word_color (str): Foreground color for user input. Available: same as above.
        strip (bool): If True, strip whitespace from result.
        pattern (str): Regex pattern for validation.
    """

    def __init__(
        self,
        prompt: str = "",
        default: str = "",
        indent: int = 0,
        prompt_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
        strip: bool = False,
        pattern: str = "",
    ):
        self.indent = indent
        if not prompt:
            raise ValueError("Prompt can not be empty!")
        self.default = f"[{default}]: " if default else ""
        self.prompt = prompt
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        self.word_color = utils.resolve_color(word_color, colors.foreground)
        self.strip = strip
        self.pattern = pattern

    def valid(self, ans):
        if not bool(re.match(self.pattern, ans)):
            utils.moveCursorUp(1)
            utils.forceWrite(" " * self.indent + self.prompt + self.default)
            utils.forceWrite(" " * len(ans))
            utils.forceWrite("\b" * len(ans))
            return False
        return True

    def launch(self):
        utils.forceWrite(
            " " * self.indent
            + self.prompt_color
            + self.prompt
            + self.default
            + colors.RESET
        )
        sess = myInput(word_color=self.word_color)
        if not self.pattern:
            while True:
                result = sess.input()
                if result == "":
                    if self.default != "":
                        return self.default[1:-1]
                    else:
                        utils.moveCursorUp(1)
                        utils.forceWrite(
                            " " * self.indent
                            + self.prompt_color
                            + self.prompt
                            + self.default
                            + colors.RESET
                        )
                        utils.forceWrite(" " * len(result))
                        utils.forceWrite("\b" * len(result))
                else:
                    break
        else:
            while True:
                result = sess.input()
                if self.valid(result):
                    break
        return result.strip() if self.strip else result


class Password:
    """
    Password input prompt for CLI with color and masking support.

    Args:
        prompt (str): Prompt text.
        indent (int): Indentation from left.
        hidden (str): Character to display for masked input.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        word_color (str): Foreground color for user input. Available: same as above.
    """

    def __init__(
        self,
        prompt: str = "",
        indent: int = 0,
        hidden: str = "*",
        prompt_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
    ):
        self.indent = indent
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        if not prompt:
            raise ValueError("Prompt can not be empty!")
        self.prompt = prompt
        self.hidden = hidden
        self.word_color = utils.resolve_color(word_color, colors.foreground)

    def launch(self):
        utils.forceWrite(
            " " * self.indent + self.prompt_color + self.prompt + colors.RESET
        )
        return myInput(
            password=True, hidden=self.hidden, word_color=self.word_color
        ).input()


class Numbers:
    """
    Numeric input prompt for CLI with color and type validation.

    Args:
        prompt (str): Prompt text.
        indent (int): Indentation from left.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        word_color (str): Foreground color for user input. Available: same as above.
        type (type): Type to cast input (int, float, etc.).
    """

    def __init__(
        self,
        prompt: str = "",
        indent: int = 0,
        prompt_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
        type=float,
    ):
        self.indent = indent
        if not prompt:
            raise ValueError("Prompt can not be empty!")
        self.prompt = prompt
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        self.word_color = utils.resolve_color(word_color, colors.foreground)
        self.type = type

    def valid(self, ans):
        try:
            self.type(ans)
            return True
        except Exception:
            utils.moveCursorUp(1)
            utils.forceWrite(
                " " * self.indent + self.prompt_color + self.prompt + colors.RESET
            )
            utils.forceWrite(" " * len(ans))
            utils.forceWrite("\b" * len(ans))
            return False

    def launch(self, default=None):
        if default is not None:
            try:
                self.type(default)
            except Exception:
                raise ValueError("`default` should be a " + str(self.type)) from None
        my_input = myInput(word_color=self.word_color)
        utils.forceWrite(
            " " * self.indent + self.prompt_color + self.prompt + colors.RESET
        )
        while True:
            ans = my_input.input()
            if ans == "" and default is not None:
                return default
            if not self.valid(ans):
                continue
            else:
                return self.type(ans)


class VerticalPrompt:
    """
    Vertical multi-component prompt for CLI with color and separator customization.

    Args:
        components (list): List of prompt components.
        spacing (int): Spacing between components.
        separator (str): Separator string.
        separator_color (str): Foreground color for separator. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
    """

    def __init__(
        self,
        components,
        spacing=1,
        separator="",
        separator_color=colors.foreground["default"],
    ):
        if not components:
            raise ValueError("Prompt components cannot be empty!")
        self.components = components
        self.spacing = spacing
        self.separator = separator
        self.separator_color = utils.resolve_color(separator_color, colors.foreground)
        self.separator_len = len(
            max(self.components, key=lambda ui: len(ui.prompt)).prompt
        )
        self.result = []

    def summarize(self):
        for prompt, answer in self.result:
            print(prompt, answer)

    def launch(self):
        self.result = []
        for ui in self.components:
            self.result.append((ui.prompt, ui.launch()))
            if not self.separator:
                utils.forceWrite("\n" * self.spacing)
            else:
                utils.cprint(
                    self.separator * self.separator_len, color=self.separator_color
                )
        return self.result


@keyhandler.init
class ScrollBar:
    """
    Scrollable list selector for CLI with color and pointer customization.

    Args:
        prompt (str): Prompt text.
        choices (list): List of choices to display.
        pointer (str): Pointer character for selection.
        up_indicator (str): Up arrow indicator.
        down_indicator (str): Down arrow indicator.
        prompt_color (str): Foreground color for prompt. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        pointer_color (str): Foreground color for pointer. Available: same as above.
        indicator_color (str): Foreground color for indicators. Available: same as above.
        word_color (str): Foreground color for choices. Available: same as above.
        word_on_switch (str): Foreground color for selected choice. Available: same as above, or colors.REVERSE.
        background_color (str): Background color for choices. Available: black, red, green, yellow, blue, magenta, cyan, white, default.
        background_on_switch (str): Background color for selected choice. Available: same as above, or colors.REVERSE.
        pad_right (int): Padding to the right of choices.
        indent (int): Indentation from left.
        align (int): Additional alignment spaces.
        margin (int): Margin between pointer and text.
        shift (int): Lines to shift down after prompt.
        height (int): Number of visible rows.
        return_index (bool): If True, return (choice, index).
    """

    def __init__(
        self,
        prompt: str = "",
        choices: list = None,
        pointer="→",
        up_indicator: str = "↑",
        down_indicator: str = "↓",
        prompt_color: str = colors.foreground["default"],
        pointer_color: str = colors.foreground["default"],
        indicator_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
        word_on_switch: str = colors.REVERSE,
        background_color: str = colors.background["default"],
        background_on_switch: str = colors.REVERSE,
        pad_right=0,
        indent: int = 0,
        align=0,
        margin: int = 0,
        shift: int = 0,
        height=None,
        return_index: bool = False,
    ):
        if not choices:
            raise ValueError("Choices can not be empty!")
        if indent < 0:
            raise ValueError("Indent must be > 0!")
        if margin < 0:
            raise ValueError("Margin must be > 0!")

        self.prompt = prompt
        self.prompt_color = utils.resolve_color(prompt_color, colors.foreground)
        self.choices = choices
        self.pos = 0  # Position of item at current cursor.

        self.indent = indent
        self.align = align
        self.margin = margin
        self.shift = shift
        self.pad_right = pad_right
        self.pointer = pointer
        self.up_indicator = up_indicator
        self.down_indicator = down_indicator

        self.pointer_color = utils.resolve_color(pointer_color, colors.foreground)
        self.indicator_color = utils.resolve_color(indicator_color, colors.foreground)
        self.word_color = utils.resolve_color(word_color, colors.foreground)
        self.word_on_switch = utils.resolve_color(word_on_switch, colors.foreground)
        self.background_color = utils.resolve_color(background_color, colors.background)
        self.background_on_switch = utils.resolve_color(background_on_switch, colors.background)

        self.max_width = len(max(self.choices, key=len)) + self.pad_right
        self.height = min(
            len(self.choices),  # Size of the scrollbar window.
            height if height else len(self.choices),
        )

        self.top = 0  # Position of the top-most item rendered.
        # scrollbar won't move if pos is in range [top, top + height)
        # scrollbar moves up if pos < top
        # scrollbar moves down if pos > top + height - 1

        self.return_index = return_index

    def renderRows(self):
        self.printRow(self.top, indicator=self.up_indicator if self.top != 0 else " ")
        utils.forceWrite("\n")

        i = self.top
        for i in range(self.top + 1, self.top + self.height - 1):
            self.printRow(i)
            utils.forceWrite("\n")

        if i < len(self.choices) - 1:
            self.printRow(
                i + 1,
                indicator=self.down_indicator
                if self.top + self.height != len(self.choices)
                else "",
            )
            utils.forceWrite("\n")

    def printRow(self, idx, indicator=""):
        utils.forceWrite(" " * (self.indent + self.align))
        back_color = (
            self.background_on_switch if idx == self.pos else self.background_color
        )
        word_color = self.word_on_switch if idx == self.pos else self.word_color

        if idx == self.pos:
            utils.cprint(
                "{}".format(self.pointer) + " " * self.margin,
                self.pointer_color,
                back_color,
                end="",
            )
        else:
            utils.cprint(
                " " * (len(self.pointer) + self.margin),
                self.pointer_color,
                back_color,
                end="",
            )
        utils.cprint(self.choices[idx], word_color, back_color, end="")
        utils.cprint(
            " " * (self.max_width - len(self.choices[idx])), on=back_color, end=""
        )
        utils.cprint(indicator, color=self.indicator_color, end="")
        utils.moveCursorHead()

    @keyhandler.register(char.ARROW_UP_KEY)
    def moveUp(self):
        if self.pos == self.top:
            if self.top == 0:
                return  # Already reached top-most position
            else:
                utils.clearConsoleDown(self.height)
                self.pos, self.top = self.pos - 1, self.top - 1
                self.renderRows()
                utils.moveCursorUp(self.height)
        else:
            utils.clearLine()
            old_pos = self.pos
            self.pos -= 1
            show_arrow = (
                old_pos == self.top + self.height - 1
                and self.top + self.height < len(self.choices)
            )
            self.printRow(old_pos, indicator=self.down_indicator if show_arrow else "")
            utils.moveCursorUp(1)
            self.printRow(self.pos)

    @keyhandler.register(char.ARROW_DOWN_KEY)
    def moveDown(self):
        if self.pos == self.top + self.height - 1:
            if self.top + self.height == len(self.choices):
                return
            else:
                utils.moveCursorDown(self.height - (self.pos - self.top + 1))
        else:
            utils.moveCursorDown(self.height - (self.pos - self.top + 1))
        utils.clearConsoleUp(self.height)
        utils.moveCursorDown(1)
        self.top = min(len(self.choices) - self.height, self.top + self.height)
        self.pos = min(len(self.choices) - 1, self.pos + self.height)
        self.renderRows()
        utils.moveCursorUp(1 + self.height - (self.pos - self.top + 1))

    @keyhandler.register(char.HOME_KEY)
    def moveTop(self):
        if self.pos == self.top:
            if self.top == 0:
                return  # Already reached top-most position
            else:
                pass  # Not at top-most position
        else:
            utils.moveCursorUp(self.pos - self.top)
        utils.clearConsoleDown(self.height)
        self.pos = self.top = 0
        self.renderRows()
        utils.moveCursorUp(self.height)

    @keyhandler.register(char.END_KEY)
    def moveBottom(self):
        if self.pos == self.top + self.height - 1:
            if self.top + self.height == len(self.choices):
                return  # Already reached bottom-most position
            else:
                pass  # Not already at bottm-most position
        else:
            utils.moveCursorDown(self.height - (self.pos - self.top + 1))
        utils.clearConsoleUp(self.height)
        utils.moveCursorDown(1)
        self.top = len(self.choices) - self.height
        self.pos = len(self.choices) - 1
        self.renderRows()
        utils.moveCursorUp(1)

    @keyhandler.register(char.PG_UP_KEY)
    def movePgUp(self):
        if self.pos == self.top:
            if self.top == 0:
                return  # Already reached top-most position
            else:
                pass  # Not at top-most position
        else:
            utils.moveCursorUp(self.pos - self.top)
        utils.clearConsoleDown(self.height)
        self.top = max(0, self.top - self.height)
        self.pos = max(0, self.pos - self.height)
        self.renderRows()
        utils.moveCursorUp(self.height - (self.pos - self.top))

    @keyhandler.register(char.PG_DOWN_KEY)
    def movePgDown(self):
        if self.pos == self.top + self.height - 1:
            if self.top + self.height == len(self.choices):
                return  # Already reached bottom-most position
            else:
                utils.moveCursorDown(self.height - (self.pos - self.top + 1))
        else:
            utils.moveCursorDown(self.height - (self.pos - self.top + 1))
        utils.clearConsoleUp(self.height)
        utils.moveCursorDown(1)
        self.top = min(len(self.choices) - self.height, self.top + self.height)
        self.pos = min(len(self.choices) - 1, self.pos + self.height)
        self.renderRows()
        utils.moveCursorUp(1 + self.height - (self.pos - self.top + 1))

    @keyhandler.register(char.NEWLINE_KEY)
    def accept(self):
        d = self.top + self.height - self.pos
        utils.moveCursorDown(d)
        ret = self.choices[self.pos]
        if self.return_index:
            return ret, self.pos
        self.pos = 0
        return ret

    @keyhandler.register(char.INTERRUPT_KEY)
    def interrupt(self):
        d = self.top + self.height - self.pos
        utils.moveCursorDown(d)
        raise KeyboardInterrupt

    def launch(self):
        if self.prompt:
            utils.forceWrite(
                " " * self.indent
                + self.prompt_color
                + self.prompt
                + colors.RESET
                + "\n"
            )
            utils.forceWrite("\n" * self.shift)
        self.renderRows()
        utils.moveCursorUp(self.height)
        with cursor.hide():
            while True:
                ret = self.handle_input()
                if ret is not None:
                    return ret


class SlidePrompt:
    """
    Horizontal multi-component prompt for CLI.

    Args:
        components (list): List of prompt components.
    """

    def __init__(self, components):
        self.idx = 0
        self.components = components
        if not components:
            raise ValueError("Prompt components cannot be empty!")
        self.result = []

    def summarize(self):
        for prompt, answer in self.result:
            print(prompt, answer)

    def launch(self):
        self.result = []
        for ui in self.components:
            self.result.append((ui.prompt, ui.launch()))
            d = 1
            if type(ui).__name__ == "Bullet" or type(ui).__name__ == "Check":
                d = 1 + ui.shift + len(ui.choices)
            utils.clearConsoleUp(d + 1)
            utils.moveCursorDown(1)
        return self.result


class Date(Input):
    """Prompt user for a `date` value until successfully parsed.

    String provided by user can be provided in any format recognized by
    `dateutil.parser`.

    Args:_
        prompt (str): Required. Text to display to user before input prompt.
        default (date): Optional. Default `date` value if user provides no
            input.
        format_str (str): Format string used to display default value,
            defaults to '%m/%d/%Y'
        indent (int): Distance between left-boundary and start of prompt.
        word_color (str): Optional. The color of the prompt and user input.
    """

    def __init__(
        self,
        prompt: str,
        default: date = None,
        format_str: str = "%m/%d/%Y",
        indent: int = 0,
        word_color: str = colors.foreground["default"],
    ):
        if default:
            default = default.strftime(format_str)
        super().__init__(prompt, default=default, indent=indent, word_color=utils.resolve_color(word_color, colors.foreground))

    def launch(self):
        while True:
            result = super().launch()
            if not result:
                continue
            try:
                date = date_parser.parse(result)
                return date.date()
            except ValueError:
                error = f"Error! '{result}' could not be parsed as a valid date.\n"
                help = (
                    "You can use any format recognized by dateutil.parser."
                    " For example, all of "
                    "the strings below are valid ways to represent the same date:\n"
                )
                examples = '\n"2018-5-13" -or- "05/13/2018" -or- "May 13 2018"\n'
                utils.cprint(error, color=colors.bright(colors.foreground["red"]))
                utils.cprint(
                    wrap_text(help, max_len=70), color=colors.foreground["red"]
                )
                utils.cprint(examples, color=colors.foreground["red"])
