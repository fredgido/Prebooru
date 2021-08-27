# SETUP.PY

# ## PYTHON IMPORTS
import pathlib
from setuptools import setup, find_packages

# INITIALIZATION


here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='prebooru',
    version='1.0'
    description='Local database for storing images',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/BrokenEagle/prebooru',
    author='BrokenEagle',
    author_email='BrokenEagle98@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Danbooru users',
        'Topic :: Database :: Images',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='image, downloader, database, danbooru',
    packages=find_packages(),
    python_requires='>=3.7, <4',
    install_requires=['flask', 'sqlalchemy', 'wtforms', 'requests', 'iso8601'],
    project_urls={
        'Bug Reports': 'https://github.com/BrokenEagle/prebooru/issues',
        'Source': 'https://github.com/BrokenEagle/prebooru/',
    },
)
