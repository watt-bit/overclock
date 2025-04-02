from setuptools import setup, find_packages

setup(
    name="Overclock",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'numpy>=1.19.0',
        'matplotlib>=3.3.0',
    ],
) 