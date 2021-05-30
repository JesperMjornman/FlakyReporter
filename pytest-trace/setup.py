from setuptools import setup

setup(
    name="pytest-trace",
    #packages=["myproject"],
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["pytest_trace = pytest_trace"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
)