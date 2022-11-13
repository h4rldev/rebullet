from setuptools import find_packages, setup

setup(
      name='rebullet',
      version='2.2.2.2',
      description='Beautiful Python prompts made simple.',
      url='https://github.com/h4rldev/rebullet',
      keywords = "cli list prompt customize colors",
      author='bchao1, h4rldev and Maintainers',
      license='MIT',
      include_package_data=True,
      packages=find_packages(),
      python_requires=">=3.10",
      install_requires=["python-dateutil"],
)
