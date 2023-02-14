""""Setup imports"""

from pathlib import Path
from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "PYPI_README.md").read_text()

setup(
  name="rebullet",
  version="2.3.3",
  description="Beautiful Python prompts made simple.",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/h4rldev/rebullet",
  keywords="cli list prompt customize colors",
  author="bchao1, h4rldev and Maintainers",
  license="MIT",
  include_package_data=True,
  packages=find_packages(),
  python_requires=">=3.10",
  install_requires=["python-dateutil"],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.10',
  ]
)
