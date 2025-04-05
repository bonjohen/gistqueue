"""
Setup script for the GistQueue package.
"""
from setuptools import setup, find_packages
import os
import re

# Read the version from the package's __init__.py file
with open(os.path.join('gistqueue', '__init__.py'), 'r') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in __init__.py")

# Read the long description from README.md
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='gistqueue',
    version=version,
    description='A message queue system using GitHub Gists',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='GistQueue Team',
    author_email='example@example.com',
    url='https://github.com/example/gistqueue',
    packages=find_packages(),
    install_requires=[
        'PyGithub>=2.0.0',
        'python-dotenv>=0.15.0',
        'requests>=2.25.0',
    ],
    entry_points={
        'console_scripts': [
            'gistqueue=gistqueue.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
)
