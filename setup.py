#!/usr/bin/env python3
"""
Setup script for Script Adapter
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines() 
                   if line.strip() and not line.startswith("#")]

setup(
    name="storyloom",
    version="1.0.0",
    author="StoryLoom Contributors",
    author_email="",
    description="故事织机 - 将剧本编织成视觉制作方案的AI增强工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/looneyren/StoryLoom",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "storyloom=script_adapter:main",
        ],
    },
    keywords=[
        "script", "screenplay", "storyboard", "anime", "ai", "video", 
        "film", "production", "animation", "text-to-image", "prompt"
    ],
    project_urls={
        "Bug Reports": "https://github.com/looneyren/StoryLoom/issues",
        "Source": "https://github.com/looneyren/StoryLoom",
        "Documentation": "https://github.com/looneyren/StoryLoom#readme",
    },
)