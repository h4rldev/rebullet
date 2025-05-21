"""Star imports"""

from rebullet import Bullet, colors

cli = Bullet(
    prompt="\nPlease choose a fruit: ",
    choices=["apple", "banana", "orange", "watermelon", "strawberry"],
    indent=0,
    align=5,
    margin=2,
    bullet="★",
    bullet_color=colors.bright("cyan", colors.foreground),
    word_color=colors.bright("yellow", colors.foreground),
    word_on_switch=colors.bright("yellow", colors.foreground),
    background_color="black",
    background_on_switch="black",
    pad_right=5,
)

result = cli.launch()
print("You chose:", result)
