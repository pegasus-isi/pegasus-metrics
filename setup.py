import os
from setuptools import setup

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pegasus-metrics",
    version = "0.1",
    author = "Gideon Juve",
    author_email = "juve@isi.edu",
    description = "Anonymous usage metrics collection and reporting for Pegasus",
    long_description = read("README.md"),
    license = "Apache2",
    url = "http://pegasus.isi.edu/metrics",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages = ["pegasus","pegasus.metrics"],
    zip_safe = False,
    install_requires = [
        "Flask==0.9"
    ]
)

