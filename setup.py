from setuptools import setup, find_packages

setup(
      name='bullet',
      version='2.2.1',
      description='Beautiful Python prompts made simple.',
      long_description="Extensive support for Python list prompts \
            formatting and colors",
      url='https://github.com/h4rldev/bullet-fork',
      keywords = "cli list prompt customize colors",
      author='Mckinsey666 and Maintainers',
      license='MIT',
      packages=find_packages(),
      python_requires=">=3.10",
      install_requires=["python-dateutil"],
)
