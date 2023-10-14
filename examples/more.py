"""More imports"""

from rebullet import Check, styles

client = Check(prompt="Choose from a list: ", **styles.Example, **styles.Exam)
print("\n", end="")
result = client.launch()
print(result)
