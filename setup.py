import os
import sys
from setuptools import setup

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# The packages we depend on
dependencies = [
    "Flask==0.9",
    "MySQL-python==1.2.5",
    "repoze.lru==0.5",
    "WTForms==1.0.3",
    "requests==1.1.0"
]

# If old Python, then we need simplejson
if sys.version_info < (2,6):
    dependencies += ["simplejson>=2.6.2"]

setup(
    name = "pegasus-metrics",
    version = "0.1",
    author = "Pegasus Team",
    author_email = "pegasus@isi.edu",
    description = "Anonymous usage metrics collection and reporting for Pegasus",
    long_description = read("README.md"),
    license = "Apache2",
    url = "https://github.com/pegasus-isi/pegasus-metrics",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages = ["pegasus","pegasus.metrics"],
    package_data = {"pegasus.metrics" : ["templates/*", "static/*"] },
    include_package_data = True,
    zip_safe = False,
    scripts = ["bin/pegasus-metrics-server", "bin/pegasus-metrics-loader"],
    install_requires = dependencies
)

