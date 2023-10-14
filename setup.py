""""Setup imports"""

from setuptools import find_packages, setup

setup(
    name="rebullet",
    version="2.4.1",
    description="Beautiful Python prompts made simple.",
    long_description=open("PYPI_README.md").read(),
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
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
)
