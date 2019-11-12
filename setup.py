"""Setup."""

from setuptools import setup, find_packages

inst_reqs = [
    "rio-cogeo>=1.1.5",
    "wget"
]
extra_reqs = {"test": ["pytest", "pytest-cov"]}

setup(
    name="app",
    version="0.0.2",
    description=u"cogeo watchbot",
    python_requires=">=3",
    keywords="AWS-Lambda Python",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
