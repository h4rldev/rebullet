"""Prompt imports"""

from rebullet import Bullet, Check, Input, Numbers, SlidePrompt, YesNo, colors

cli = SlidePrompt(
    [
        YesNo("Are you a student? ",
            word_color="yellow"),
        YesNo("Are you a good student? ",
            default='y',
            word_color="yellow"),
        Input("Who are you? ",
            default="Batman",
            word_color="yellow"),
        Input("Really? ",
            word_color="yellow"),
        Numbers("How old are you? ",
            word_color="yellow",
            type=int),
        Bullet("What is your favorite programming language? ",
            choices=["C++", "Python", "Javascript", "Not here!"],
            bullet=" >",
            margin=2,
            bullet_color=colors.bright("cyan", colors.foreground),
            background_color="black",
            background_on_switch="black",
            word_color="white",
            word_on_switch="white"
        ),
        Check("What food do you like? ",
            choices=["🍣   Sushi",
                     "🍜   Ramen",
                     "🌭   Hotdogs",
                     "🍔   Hamburgers",
                     "🍕   Pizza",
                     "🍝   Spaghetti",
                     "🍰   Cakes",
                     "🍩   Donuts"],
            check=" √",
            margin=2,
            check_color=colors.bright("red", colors.foreground),
            check_on_switch=colors.bright("red", colors.foreground),
            background_color="black",
            background_on_switch="white",
            word_color="white",
            word_on_switch="black"
        ),
    ]
)

print("\n")
result = cli.launch()
cli.summarize()
