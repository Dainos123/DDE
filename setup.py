from setuptools import setup, find_packages

setup(
    name="kubernetes_dde",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "scipy>=1.7.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
)
