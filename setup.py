#!/usr/bin/env python
"""Setup script for helix-narrative-engine"""

from setuptools import setup, find_packages

setup(
    name="helix-narrative-engine",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "google-generativeai>=0.3.0",
        "xai-sdk>=0.1.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "isort>=5.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "sphinx>=6.0",
        ],
    },
    author="Helix Team",
    author_email="team@helix.dev",
    description="Multi-LLM creative content generation with agent specialization",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Deathcharge/helix-narrative-engine",
    project_urls={
        "Bug Tracker": "https://github.com/Deathcharge/helix-narrative-engine/issues",
        "Documentation": "https://github.com/Deathcharge/helix-narrative-engine#readme",
        "Source Code": "https://github.com/Deathcharge/helix-narrative-engine",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    license="Apache-2.0",
    keywords=[
        "ai",
        "creative",
        "narrative",
        "storytelling",
        "multi-llm",
        "agents",
        "content-generation",
    ],
)
