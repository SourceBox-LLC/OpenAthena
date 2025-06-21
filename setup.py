import os
import sys
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from pathlib import Path
import getpass

# Read the long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def configure_opens3():
    """
    Interactive configuration of OpenS3 connection settings
    Creates a .env file with appropriate environment variables
    """
    print("\n" + "=" * 50)
    print("OpenAthena - OpenS3 Connection Configuration")
    print("=" * 50)

    # Default settings for the Raspberry Pi server
    default_endpoint = "http://10.0.0.204:80"

    # Get input from user with defaults
    print("\nEnter your OpenS3 connection details (press Enter to use defaults):")

    endpoint = (
        input(f"OpenS3 Endpoint URL [default: {default_endpoint}]: ").strip()
        or default_endpoint
    )

    # For security, don't show default credentials and always prompt
    access_key = input("OpenS3 Access Key: ").strip()
    if not access_key:
        print("Warning: Access Key is required for OpenS3 access")

    # Use getpass for the secret key to avoid showing it in the terminal
    secret_key = getpass.getpass("OpenS3 Secret Key: ").strip()
    if not secret_key:
        print("Warning: Secret Key is required for OpenS3 access")

    # Ask if the user wants to create the .env file
    create_env = (
        input("\nCreate .env file with these settings? (y/n) [default: y]: ")
        .strip()
        .lower()
        or "y"
    )

    if create_env == "y":
        env_path = Path(".env")

        # Create or overwrite the .env file
        with open(env_path, "w") as env_file:
            env_file.write(f"# OpenAthena Environment Configuration\n")
            env_file.write(f"# Created by OpenAthena setup.py\n\n")

            # OpenS3 connection settings
            env_file.write(f"# OpenS3 Connection Settings\n")
            env_file.write(f"OPENS3_ENDPOINT={endpoint}\n")
            if access_key:
                env_file.write(f"OPENS3_ACCESS_KEY={access_key}\n")
            if secret_key:
                env_file.write(f"OPENS3_SECRET_KEY={secret_key}\n")

            # Additional optional settings with comments
            env_file.write(f"\n# Optional OpenAthena Settings\n")
            env_file.write(f"# OPENATHENA_CATALOG_PATH=catalog.yml\n")
            env_file.write(f"# OPENATHENA_DB_PATH=openathena.db\n")
            env_file.write(f"# OPENATHENA_HOST=0.0.0.0\n")
            env_file.write(f"# OPENATHENA_PORT=8000\n")
            env_file.write(f"# OPENATHENA_THREADS=4\n")
            env_file.write(f"# OPENATHENA_MEMORY_LIMIT=4GB\n")

        print(f"\n✅ .env file created successfully at: {env_path.absolute()}")
        print("You can edit this file later to update your configuration.")
    else:
        print("\nSkipped .env file creation.")

    print("\nTo start the OpenAthena server:")
    print("  python -m open_athena.api")
    print("\nFor more information, see the README.md file.")
    print("=" * 50 + "\n")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def __init__(self, *args, **kwargs):
        super(PostDevelopCommand, self).__init__(*args, **kwargs)
        self.no_configure = False

    def initialize_options(self):
        develop.initialize_options(self)
        self.no_configure = False

    def finalize_options(self):
        develop.finalize_options(self)

    def run(self):
        develop.run(self)

        # Check environment variable for configuration skip
        if os.environ.get("OPENATHENA_SKIP_CONFIGURE") == "true":
            return

        # Ask if the user wants to configure OpenS3
        configure = (
            input(
                "\nWould you like to configure OpenS3 connection settings? (y/n) [default: y]: "
            )
            .strip()
            .lower()
            or "y"
        )
        if configure == "y":
            configure_opens3()


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def __init__(self, *args, **kwargs):
        super(PostInstallCommand, self).__init__(*args, **kwargs)
        self.no_configure = False

    def initialize_options(self):
        install.initialize_options(self)
        self.no_configure = False

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        install.run(self)

        # Check environment variable for configuration skip
        if os.environ.get("OPENATHENA_SKIP_CONFIGURE") == "true":
            return

        # Ask if the user wants to configure OpenS3
        configure = (
            input(
                "\nWould you like to configure OpenS3 connection settings? (y/n) [default: y]: "
            )
            .strip()
            .lower()
            or "y"
        )
        if configure == "y":
            configure_opens3()


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
            "configure-opens3=open_athena.main:configure_opens3",
        ],
    },
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
)
