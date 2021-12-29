from setuptools import setup

setup(name='tee-output',
      version='0.2',
      description='A utility to tee standard output / standard error from the current process into a logfile. Preserves terminal semantics, so breakpoint() etc continue to work.',
      author='Greg Brockman',
      packages=['tee_output'],
      scripts=["bin/parent-lifetime"]
)
