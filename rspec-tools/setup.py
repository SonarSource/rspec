from setuptools import setup, find_packages

setup(
    name='rspec-tools',
    version='1.0.0',
    url='https://github.com/SonarSource/rspec',
    author='SonarSource',
    description='Rule specification tooling',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['rspec-tools = rspec_tools:cli']
    },
)