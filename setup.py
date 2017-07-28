from setuptools import setup, find_packages
from shapeup_views import __author__, __version__, __license__

setup(
    name = 'django-shapeup-views',
    version = __version__,
    description = 'shapeup class based views.',
    license = __license__,
    author = __author__,
    author_email = 'yamagata@clouds-inc.jp',
    url = 'https://github.com/instorm/django-shapeup-views',
    keywords = 'django python',
    packages = find_packages(),
    install_requires = [],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', 
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)

