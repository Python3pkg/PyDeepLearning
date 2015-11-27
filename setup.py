from distutils.core import setup

setup(
    name='PyDeepLearning',
    version='0.1',
    packages=['pydl'],
    url='https://github.com/frugs/PyDeepLearning',
    license='MIT',
    author='hugo',
    author_email='frugs@github.com',
    description='Deep learning neural network implementation with backprop using numpy.',
    data_files=[("", ["LICENSE.txt"])],
    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 3']
)
