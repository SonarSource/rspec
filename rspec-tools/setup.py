from setuptools import setup, find_packages

setup(
    name='rspec-tools',
    version='1.0.0',
    author='SonarSource',
    description='Rule specification tooling',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['rspec-tools = rspec_tools:cli']
    },
)