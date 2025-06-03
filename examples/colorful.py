"""Colorful imports"""

from rebullet import Bullet

cli = Bullet(
        prompt = "\nPlease choose a fruit: ",
        choices = ["apple", "banana", "orange", "watermelon", "strawberry"],
        indent = 0,
        align = 5,
        margin = 2,
        shift = 0,
        bullet = "●",
        bullet_color="magenta",
        word_color="red",
        word_on_switch="green",
        background_color="cyan",
        background_on_switch="yellow",
        pad_right = 5
    )

result = cli.launch()
print("You chose:", result)
