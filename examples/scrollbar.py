"""Scrollbar imports"""

from rebullet import ScrollBar, colors, emojis

cli = ScrollBar(
    "How are you feeling today? ",
    emojis.feelings[0],
    height = 5,
    align = 5,
    margin = 0,
    pointer = "👉",
    background_on_switch = 'default',
    word_on_switch = 'default',
    return_index = True
)
print("\n")
result = cli.launch()
print(result)
