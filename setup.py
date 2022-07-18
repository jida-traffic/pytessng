import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
  name="opendrive2tess",
  version="0.0.5",
  author="Author",
  author_email="17315487709@163.com",
  description="convert opendrive info to create tess network",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="",
  install_requires=[
    'matplotlib',
    'lxml>=4.9.1',
    'matlab>=0.1',
    'numpy>=1.19.5',
    'scipy>=1.5.4',
    'commonroad.io>=2020.2',
  ],
  python_requires='>=3.6, <=3.9',
  packages=setuptools.find_packages(),
  classifiers=[
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
  ],
)