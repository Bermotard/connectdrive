from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="connectdrive",
    version="1.0.0",
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Outil de montage de partages réseau avec interface graphique",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bermotard/connectdrive",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "python-dotenv>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "connectdrive=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
)
