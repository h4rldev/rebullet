"""Client imports."""

import re
from collections import defaultdict
from datetime import date

from dateutil import parser as date_parser

from . import charDef as char
from . import colors, cursor, keyhandler, utils
from .exceptions import MissingDependenciesError
from .wrap_text import wrap_text

PROMPT_EMPTY_ERROR = "Prompt can not be empty!"
CHOICES_EMPTY_ERROR = "Choices can not be empty!"
INDENT_ERROR = "Indent must be > 0!"
MARGIN_ERROR = "Margin must be > 0!"


# Reusable private utility class
class MyInput:
    def __init__(
        self,
        word_color: str = colors.foreground["default"],
        password: bool = False,
        hidden: str = "*",
    ):
        """Construct for myInput."""
        """
        Args:
            word_color: color of input characters.
            password: Whether input is password.
            hidden: Character to be outputted for password input.
        """
        self.buffer = []  # Buffer to store entered characters
        self.pos = 0  # Current cursor position
        self.password = password
        self.hidden = hidden
        self.word_color = word_color

    def move_cursor(self, pos):
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
                utils.force_write("\b")
                self.pos -= 1
        return True

    def insert_char(self, c):
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
        utils.force_write("\b" * (len(self.buffer) - self.pos - 1))
        self.pos += 1

    def get_input(self):
        """Return content in buffer."""
        ret = "".join(self.buffer)
        self.buffer = []
        self.pos = 0
        return ret

    def delete_char(self):
        """Remove character at current cursor position."""
        if self.pos == len(self.buffer):
            return
        self.buffer.pop(self.pos)
        if self.hidden:
            utils.force_write(self.hidden * (len(self.buffer) - self.pos) + " ")
        else:
            utils.force_write("".join(self.buffer[self.pos :]) + " ")
        utils.force_write("\b" * (len(self.buffer) - self.pos + 1))

    def input(self):
        while True:
            c = utils.getchar()
            i = c if c == char.UNDEFINED_KEY else ord(c)

            match i:
                case char.NEWLINE_KEY:
                    utils.force_write("\n")
                    return self.get_input()
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
                    if self.move_cursor(self.pos - 1):
                        self.delete_char()
                case char.BACK_SPACE_CHAR:
                    if self.move_cursor(self.pos - 1):
                        self.delete_char()
                case char.DELETE_KEY:
                    self.delete_char()
                case char.ARROW_RIGHT_KEY:
                    self.move_cursor(self.pos + 1)
                case char.ARROW_LEFT_KEY:
                    self.move_cursor(self.pos - 1)
                case _:
                    if self.password and c != " " or not self.password:
                        self.insert_char(c)


@keyhandler.init
class Bullet:
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
            raise ValueError(CHOICES_EMPTY_ERROR)
        if indent < 0:
            raise ValueError(INDENT_ERROR)
        if margin < 0:
            raise ValueError(MARGIN_ERROR)

        self.prompt = prompt
        self.prompt_color = prompt_color
        self.choices = choices
        self.pos = 0

        self.indent = indent
        self.align = align
        self.margin = margin
        self.shift = shift

        self.bullet = bullet
        self.bullet_color = bullet_color

        self.word_color = word_color
        self.word_on_switch = word_on_switch
        self.background_color = background_color
        self.background_on_switch = background_on_switch
        self.pad_right = pad_right

        self.max_width = len(max(self.choices, key=len)) + self.pad_right
        self.return_index = return_index

    def render_bullets(self):
        for i in range(len(self.choices)):
            self.print_bullet(i)
            utils.force_write("\n")

    def print_bullet(self, idx):
        utils.force_write(" " * (self.indent + self.align))
        back_color = (
            self.background_on_switch if idx == self.pos else self.background_color
        )
        word_color = self.word_on_switch if idx == self.pos else self.word_color
        if idx == self.pos:
            utils.cprint(
                f"{self.bullet}" + " " * self.margin,
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
        utils.move_cursor_head()

    @keyhandler.register(char.ARROW_UP_KEY)
    def move_up(self):
        if self.pos < 1:
            return
        utils.clear_line()
        old_pos = self.pos
        self.pos -= 1
        self.print_bullet(old_pos)
        utils.move_cursor_up(1)
        self.print_bullet(self.pos)

    @keyhandler.register(char.ARROW_DOWN_KEY)
    def move_down(self):
        if self.pos + 1 >= len(self.choices):
            return
        utils.clear_line()
        old_pos = self.pos
        self.pos += 1
        self.print_bullet(old_pos)
        utils.move_cursor_down(1)
        self.print_bullet(self.pos)

    @keyhandler.register(char.HOME_KEY)
    def move_top(self):
        utils.clear_line()
        old_pos = self.pos
        self.pos = 0
        self.print_bullet(old_pos)
        while old_pos > 0:
            utils.move_cursor_up(1)
            old_pos -= 1
        self.print_bullet(self.pos)

    @keyhandler.register(char.END_KEY)
    def move_bottom(self):
        utils.clear_line()
        old_pos = self.pos
        self.pos = len(self.choices) - 1
        self.print_bullet(old_pos)
        while old_pos < len(self.choices) - 1:
            utils.move_cursor_down(1)
            old_pos += 1
        self.print_bullet(self.pos)

    @keyhandler.register(char.NEWLINE_KEY)
    def accept(self):
        utils.move_cursor_down(len(self.choices) - self.pos)
        ret = self.choices[self.pos]
        if self.return_index:
            return ret, self.pos
        self.pos = 0
        return ret

    @keyhandler.register(char.INTERRUPT_KEY)
    def interrupt(self):
        utils.move_cursor_down(len(self.choices) - self.pos)
        raise KeyboardInterrupt

    def launch(self, default=None):
        if self.prompt:
            utils.force_write(
                " " * self.indent
                + self.prompt_color
                + self.prompt
                + colors.RESET
                + "\n"
            )
            utils.force_write("\n" * self.shift)
        if default is not None:
            if type(default).__name__ != "int":
                raise TypeError("'default' should be an integer value!")
            if not 0 <= int(default) < len(self.choices):
                raise ValueError("'default' should be in range [0, len(choices))!")
            self.pos = default
        self.render_bullets()
        utils.move_cursor_up(len(self.choices) - self.pos)
        with cursor.hide():
            while True:
                ret = self.handle_input()
                if ret is not None:
                    return ret


@keyhandler.init
class Check:
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
            raise ValueError(CHOICES_EMPTY_ERROR)
        if indent < 0:
            raise ValueError(INDENT_ERROR)
        if margin < 0:
            raise ValueError(MARGIN_ERROR)

        self.prompt = prompt
        self.prompt_color = prompt_color
        self.choices = choices
        self.checked = [False] * len(self.choices)
        self.pos = 0

        self.indent = indent
        self.align = align
        self.margin = margin
        self.shift = shift

        self.check_value = check
        self.check_color = check_color
        self.check_on_switch = check_on_switch

        self.word_color = word_color
        self.word_on_switch = word_on_switch
        self.background_color = background_color
        self.background_on_switch = background_on_switch
        self.pad_right = pad_right

        self.max_width = len(max(self.choices, key=len)) + self.pad_right
        self.return_index = return_index

    def render_rows(self):
        for i in range(len(self.choices)):
            self.print_row(i)
            utils.force_write("\n")

    def print_row(self, idx):
        utils.force_write(" " * (self.indent + self.align))
        back_color = (
            self.background_on_switch if idx == self.pos else self.background_color
        )
        word_color = self.word_on_switch if idx == self.pos else self.word_color
        check_color = self.check_on_switch if idx == self.pos else self.check_color
        if self.checked[idx]:
            utils.cprint(
                f"{self.check_value}" + " " * self.margin,
                check_color,
                back_color,
                end="",
            )
        else:
            utils.cprint(
                " " * (len(self.check_value) + self.margin),
                check_color,
                back_color,
                end="",
            )
        utils.cprint(self.choices[idx], word_color, back_color, end="")
        utils.cprint(
            " " * (self.max_width - len(self.choices[idx])), on=back_color, end=""
        )
        utils.move_cursor_head()

    @keyhandler.register(char.SPACE_CHAR)
    def toggle_row(self):
        self.checked[self.pos] = not self.checked[self.pos]
        self.print_row(self.pos)

    @keyhandler.register(char.ARROW_UP_KEY)
    def move_up(self):
        if self.pos < 1:
            return
        utils.clear_line()
        old_pos = self.pos
        self.pos -= 1
        self.print_row(old_pos)
        utils.move_cursor_up(1)
        self.print_row(self.pos)

    @keyhandler.register(char.ARROW_DOWN_KEY)
    def move_down(self):
        if self.pos + 1 >= len(self.choices):
            return
        utils.clear_line()
        old_pos = self.pos
        self.pos += 1
        self.print_row(old_pos)
        utils.move_cursor_down(1)
        self.print_row(self.pos)

    @keyhandler.register(char.HOME_KEY)
    def move_top(self):
        utils.clear_line()
        old_pos = self.pos
        self.pos = 0
        self.print_row(old_pos)
        while old_pos > 0:
            utils.move_cursor_up(1)
            old_pos -= 1
        self.print_row(self.pos)

    @keyhandler.register(char.END_KEY)
    def move_bottom(self):
        utils.clear_line()
        old_pos = self.pos
        self.pos = len(self.choices) - 1
        self.print_row(old_pos)
        while old_pos < len(self.choices) - 1:
            utils.move_cursor_down(1)
            old_pos += 1
        self.print_row(self.pos)

    @keyhandler.register(char.NEWLINE_KEY)
    def accept(self):
        utils.move_cursor_down(len(self.choices) - self.pos)
        ret = [self.choices[i] for i in range(len(self.choices)) if self.checked[i]]
        ret_idx = [i for i in range(len(self.choices)) if self.checked[i]]
        self.pos = 0
        self.checked = [False] * len(self.choices)
        return (ret, ret_idx) if self.return_index else ret

    @keyhandler.register(char.INTERRUPT_KEY)
    def interrupt(self):
        utils.move_cursor_down(len(self.choices) - self.pos)
        raise KeyboardInterrupt

    def launch(self, default=None):
        if self.prompt:
            utils.force_write(
                " " * self.indent
                + self.prompt_color
                + self.prompt
                + colors.RESET
                + "\n"
            )
            utils.force_write("\n" * self.shift)
        if default is None:
            default = []
        if default:
            if type(default).__name__ != "list":
                raise TypeError("`default` should be a list of integers!")
            if any(type(i).__name__ != "int" for i in default):
                raise TypeError("Indices in `default` should be integer type!")
            if not all(0 <= i < len(self.choices) for i in default):
                raise ValueError(
                    "All indices in `default` should be in range [0, len(choices))!"
                )
            for i in default:
                self.checked[i] = True
        self.render_rows()
        utils.move_cursor_up(len(self.choices))
        with cursor.hide():
            while True:
                ret = self.handle_input()
                if ret is not None:
                    return ret


class CheckDependencies(Check):
    """Extend Check to follow dependencies."""

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
        self.dependencies = dict(dep_tree)
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
        if self.pos != 0:
            utils.move_cursor_up(self.pos)
        utils.clear_line()
        self.print_row(0)
        for pos in range(1, len(self.choices)):
            utils.move_cursor_down(0)
            utils.clear_line()
            self.print_row(pos)
        if self.pos != len(self.choices) - 1:
            utils.move_cursor_up(len(self.choices) - self.pos - 1)


class YesNo:
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
            raise ValueError(PROMPT_EMPTY_ERROR)
        if default.lower() not in ["y", "n"]:
            raise ValueError("`default` can only be 'y' or 'n'!")
        self.default = f"[{default.lower()}]: "
        self.default = f"[{default.lower()}]: "
        self.prompt = prompt_prefix + prompt
        self.prompt_color = prompt_color
        self.word_color = word_color

    def valid(self, ans):
        if ans is None:
            return False
        ans = ans.lower()
        if "yes".startswith(ans) or "no".startswith(ans):
            return True
        utils.move_cursor_up(self.prompt.count("\n") + 1)
        utils.force_write(
            " " * self.indent
            + self.prompt_color
            + self.prompt
            + self.default
            + colors.RESET
        )
        utils.force_write(" " * len(ans))
        utils.force_write("\b" * len(ans))
        return False

    def launch(self):
        my_input = MyInput(word_color=self.word_color)
        utils.force_write(
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
            raise ValueError(PROMPT_EMPTY_ERROR)
        self.default = f"[{default}]: " if default else ""
        self.prompt = prompt
        self.prompt_color = prompt_color
        self.word_color = word_color
        self.strip = strip
        self.pattern = pattern

    def valid(self, ans):
        if not bool(re.match(self.pattern, ans)):
            utils.move_cursor_up(1)
            utils.force_write(" " * self.indent + self.prompt + self.default)
            utils.force_write(" " * len(ans))
            utils.force_write("\b" * len(ans))
            return False
        return True

    def launch(self):
        utils.force_write(
            " " * self.indent
            + self.prompt_color
            + self.prompt
            + self.default
            + colors.RESET
        )
        sess = MyInput(word_color=self.word_color)
        if not self.pattern:
            while True:
                result = sess.input()
                if result != "":
                    break
                if self.default != "":
                    return self.default[1:-1]
                utils.move_cursor_up(1)
                utils.force_write(
                    " " * self.indent
                    + self.prompt_color
                    + self.prompt
                    + self.default
                    + colors.RESET
                )
                utils.force_write(" " * len(result))
                utils.force_write("\b" * len(result))
        else:
            while True:
                result = sess.input()
                if self.valid(result):
                    break
        return result.strip() if self.strip else result


class Password:
    def __init__(
        self,
        prompt: str = "",
        indent: int = 0,
        hidden: str = "*",
        prompt_color: str = colors.foreground["default"],
        word_color: str = colors.foreground["default"],
    ):
        self.indent = indent
        self.prompt_color = prompt_color
        if not prompt:
            raise ValueError(PROMPT_EMPTY_ERROR)
        self.prompt = prompt
        self.hidden = hidden
        self.word_color = word_color

    def launch(self):
        utils.force_write(
            " " * self.indent + self.prompt_color + self.prompt + colors.RESET
        )
        return MyInput(
            password=True, hidden=self.hidden, word_color=self.word_color
        ).input()


class Numbers:
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
            raise ValueError(PROMPT_EMPTY_ERROR)
        self.prompt = prompt
        self.prompt_color = prompt_color
        self.word_color = word_color
        self.type = type

    def valid(self, ans):
        try:
            self.type(ans)
            return True
        except Exception:
            utils.move_cursor_up(1)
            utils.force_write(
                " " * self.indent + self.prompt_color + self.prompt + colors.RESET
            )
            utils.force_write(" " * len(ans))
            utils.force_write("\b" * len(ans))
            return False

    def launch(self, default=None):
        if default is not None:
            try:
                self.type(default)
            except Exception:
                raise ValueError(f"`default` should be a {str(self.type)}") from None
        my_input = MyInput(word_color=self.word_color)
        utils.force_write(
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
        self.separator_color = separator_color
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
                utils.force_write("\n" * self.spacing)
            else:
                utils.cprint(
                    self.separator * self.separator_len, color=self.separator_color
                )
        return self.result


@keyhandler.init
class ScrollBar:
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
            raise ValueError(CHOICES_EMPTY_ERROR)
        if indent < 0:
            raise ValueError(INDENT_ERROR)
        if margin < 0:
            raise ValueError(MARGIN_ERROR)

        self.prompt = prompt
        self.prompt_color = prompt_color
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

        self.pointer_color = pointer_color
        self.indicator_color = indicator_color
        self.word_color = word_color
        self.word_on_switch = word_on_switch
        self.background_color = background_color
        self.background_on_switch = background_on_switch

        self.max_width = len(max(self.choices, key=len)) + self.pad_right
        self.height = min(
            len(self.choices),  # Size of the scrollbar window.
            height or len(self.choices),
        )

        self.top = 0  # Position of the top-most item rendered.
        # scrollbar won't move if pos is in range [top, top + height)
        # scrollbar moves up if pos < top
        # scrollbar moves down if pos > top + height - 1

        self.return_index = return_index

    def render_rows(self):
        self.print_row(self.top, indicator=self.up_indicator if self.top != 0 else " ")
        utils.force_write("\n")

        i = self.top
        for i in range(self.top + 1, self.top + self.height - 1):
            self.print_row(i)
            utils.force_write("\n")

        if i < len(self.choices) - 1:
            self.print_row(
                i + 1,
                indicator=self.down_indicator
                if self.top + self.height != len(self.choices)
                else "",
            )
            utils.force_write("\n")

    def print_row(self, idx, indicator=""):
        utils.force_write(" " * (self.indent + self.align))
        back_color = (
            self.background_on_switch if idx == self.pos else self.background_color
        )
        word_color = self.word_on_switch if idx == self.pos else self.word_color

        if idx == self.pos:
            utils.cprint(
                f"{self.pointer}" + " " * self.margin,
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
        utils.move_cursor_head()

    @keyhandler.register(char.ARROW_UP_KEY)
    def move_up(self):
        if self.pos == self.top:
            if self.top == 0:
                return  # Already reached top-most position
            utils.clear_console_down(self.height)
            self.pos, self.top = self.pos - 1, self.top - 1
            self.render_rows()
            utils.move_cursor_up(self.height)
        else:
            utils.clear_line()
            old_pos = self.pos
            self.pos -= 1
            show_arrow = (
                old_pos == self.top + self.height - 1
                and self.top + self.height < len(self.choices)
            )
            self.print_row(old_pos, indicator=self.down_indicator if show_arrow else "")
            utils.move_cursor_up(1)
            self.print_row(self.pos)

    @keyhandler.register(char.ARROW_DOWN_KEY)
    def move_down(self):
        if self.pos == self.top + self.height - 1:
            if self.top + self.height == len(self.choices):
                return
            utils.clear_console_up(self.height)
            utils.move_cursor_down(1)
            self.pos, self.top = self.pos + 1, self.top + 1
            self.render_rows()
            utils.move_cursor_up(1)
        else:
            utils.clear_line()
            old_pos = self.pos
            self.pos += 1
            show_arrow = old_pos == self.top and self.top > 0
            self.print_row(old_pos, indicator=self.up_indicator if show_arrow else "")
            utils.move_cursor_down(1)
            self.print_row(self.pos)

    @keyhandler.register(char.HOME_KEY)
    def move_top(self):
        if self.pos == self.top:
            if self.top == 0:
                return  # Already reached top-most position
        else:
            utils.move_cursor_up(self.pos - self.top)
        utils.clear_console_down(self.height)
        self.pos = self.top = 0
        self.render_rows()
        utils.move_cursor_up(self.height)

    @keyhandler.register(char.END_KEY)
    def move_bottom(self):
        if self.pos == self.top + self.height - 1:
            if self.top + self.height == len(self.choices):
                return  # Already reached bottom-most position
        else:
            utils.move_cursor_down(self.height - (self.pos - self.top + 1))
        utils.clear_console_up(self.height)
        utils.move_cursor_down(1)
        self.top = len(self.choices) - self.height
        self.pos = len(self.choices) - 1
        self.render_rows()
        utils.move_cursor_up(1)

    @keyhandler.register(char.PG_UP_KEY)
    def move_page_up(self):
        if self.pos == self.top:
            if self.top == 0:
                return  # Already reached top-most position
        else:
            utils.move_cursor_up(self.pos - self.top)
        utils.clear_console_down(self.height)
        self.top = max(0, self.top - self.height)
        self.pos = max(0, self.pos - self.height)
        self.render_rows()
        utils.move_cursor_up(self.height - (self.pos - self.top))

    @keyhandler.register(char.PG_DOWN_KEY)
    def move_page_down(self):
        if self.pos == self.top + self.height - 1:
            if self.top + self.height == len(self.choices):
                return  # Already reached bottom-most position
            else:
                utils.move_cursor_down(self.height - (self.pos - self.top + 1))
        else:
            utils.move_cursor_down(self.height - (self.pos - self.top + 1))
        utils.clear_console_up(self.height)
        utils.move_cursor_down(1)
        self.top = min(len(self.choices) - self.height, self.top + self.height)
        self.pos = min(len(self.choices) - 1, self.pos + self.height)
        self.render_rows()
        utils.move_cursor_up(1 + self.height - (self.pos - self.top + 1))

    @keyhandler.register(char.NEWLINE_KEY)
    def accept(self):
        d = self.top + self.height - self.pos
        utils.move_cursor_down(d)
        ret = self.choices[self.pos]
        if self.return_index:
            return ret, self.pos
        self.pos = 0
        return ret

    @keyhandler.register(char.INTERRUPT_KEY)
    def interrupt(self):
        d = self.top + self.height - self.pos
        utils.move_cursor_down(d)
        raise KeyboardInterrupt

    def launch(self):
        if self.prompt:
            utils.force_write(
                " " * self.indent
                + self.prompt_color
                + self.prompt
                + colors.RESET
                + "\n"
            )
            utils.force_write("\n" * self.shift)
        self.render_rows()
        utils.move_cursor_up(self.height)
        with cursor.hide():
            while True:
                ret = self.handle_input()
                if ret is not None:
                    return ret


class SlidePrompt:
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
            if type(ui).__name__ in ["Bullet", "Check"]:
                d = 1 + ui.shift + len(ui.choices)
            utils.clear_console_up(d + 1)
            utils.move_cursor_down(1)
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
        super().__init__(prompt, default=default, indent=indent, word_color=word_color)

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
                help_message = (
                    "You can use any format recognized by dateutil.parser."
                    " For example, all of "
                    "the strings below are valid ways to represent the same date:\n"
                )
                examples = '\n"2018-5-13" -or- "05/13/2018" -or- "May 13 2018"\n'
                utils.cprint(error, color=colors.bright(colors.foreground["red"]))
                utils.cprint(
                    wrap_text(help_message, max_len=70), color=colors.foreground["red"]
                )
                utils.cprint(examples, color=colors.foreground["red"])
