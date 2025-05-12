#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you'll need:
#   pip install twine

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "peri-tts"
DESCRIPTION = "Text-to-Speech service for the Peri morning routine assistant"
URL = "https://github.com/periproject/peri-tts"
EMAIL = "info@periproject.com"
AUTHOR = "Peri Team"
REQUIRES_PYTHON = ">=3.8.0"
VERSION = "0.1.0"

# What packages are required for this module to be executed?
REQUIRED = [
    "fastapi>=0.103.1",
    "uvicorn>=0.23.2",
    "pydantic>=2.3.0",
    "python-multipart>=0.0.6",
    "numpy>=1.25.2",
    "soundfile>=0.12.1",
    "requests>=2.31.0",
    "kokoro-onnx>=0.4.8",
    "tqdm>=4.66.0",
    "loguru>=0.7.0",
    "aiofiles>=23.1.0",
]

# What packages are optional?
EXTRAS = {
    "dev": [
        "pytest>=7.3.1",
        "pytest-asyncio>=0.21.0",
        "httpx>=0.24.1",
        "flake8>=6.0.0",
        "mypy>=1.3.0",
        "black>=23.3.0",
    ],
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(where="src", exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_dir={"": "src"},
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
    entry_points={
        "console_scripts": [
            "peri-tts=main:main",
        ],
    },
)
