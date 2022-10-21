import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytessng",
    version="0.0.10",
    author="yang",
    author_email="17315487709@163.com",
    description="tessng with python3.6",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    install_requires=[
        'opendrive2tessng',
        'PySide2==5.15.2.1',
    ],
    python_requires='>=3.6, <3.7',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={  # Optional
            'pytessng': ['*.dll', '*.pyd', '*.py', '*.pyi'],
        },
)
