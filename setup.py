import os
import sys
from setuptools import setup

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# The packages we depend on
dependencies = [
    "Flask==0.9"
]

# If old Python, then we need simplejson
if sys.version_info < (2,6):
    dependencies += ["simplejson>=2.6.2"]

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
    packages = ["pegasus","pegasus.metrics", "pegasus.metrics.web"],
    zip_safe = False,
    install_requires = dependencies
)

