from setuptools import setup, find_packages

setup(
    name='krauler',
    version='0.1.2',
    description="A minimalistic, recursive web crawling library for Python.",
    long_description="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='',
    author='Friedrich Lindenberg',
    author_email='friedrich@pudo.org',
    url='http://pudo.org',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'six',
        'requests >= 2.5',
        'metafolder',
        'click',
        'lxml >= 3',
        'PyYAML >= 3.10',
        'urlnorm'
    ],
    entry_points={
        'console_scripts': [
            'krauler = krauler.cli:main'
        ]
    },
    tests_require=[]
)
