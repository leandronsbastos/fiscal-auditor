from setuptools import setup, find_packages

setup(
    name="fiscal-auditor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "lxml>=4.9.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
)
