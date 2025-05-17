from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="open-athena",
    version="0.1.0",
    author="SourceBox LLC",
    author_email="info@sourcebox.com",
    description="SQL analytics engine for OpenS3 powered by DuckDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SourceBox-LLC/OpenAthena",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "duckdb==1.2.2",
        "fastapi>=0.104.0",
        "uvicorn>=0.23.2",
        "pyyaml>=6.0",
        "pyarrow>=14.0.0",
        "python-multipart>=0.0.6",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "open-athena=open_athena.main:main",
        ],
    },
)
