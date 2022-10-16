from setuptools import setup, find_packages

setup(
      name='rebullet',
      version='2.2.2',
      description='Beautiful Python prompts made simple.',
      long_description="Extensive support for Python list prompts \
            formatting and colors",
      url='https://github.com/h4rldev/bullet-fork',
      keywords = "cli list prompt customize colors",
      author='bchao1, h4rldev and Maintainers',
      license='MIT',
      packages=find_packages(),
      python_requires=">=3.10",
      install_requires=["python-dateutil"],
)
