# -*- coding: utf-8 -*-
#
## SAUCE - System for AUtomated Code Evaluation
## Copyright (C) 2013 Moritz Schlarb
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# quickstarted Options:
#
# sqlalchemy: True
# auth:       sqlalchemy
# mako:       True
#

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

# Fix shutdown errors while installing
try:
    import multiprocessing  # @UnusedImport
    import logging  # @UnusedImport
except:
    pass

testpkgs = [
    'WebTest >= 1.2.3',
    'nose',
    'nose-exclude',
#    'coverage',
    'wsgiref',
    'repoze.who-testutil >= 1.0.1',
    'BeautifulSoup'
    ]

install_requires = [
    "TurboGears2 == 2.1.5",
    "Mako",
    "zope.sqlalchemy >= 0.4",
    "repoze.tm2 >= 1.0a5",
    "sqlalchemy >= 0.7, < 0.8.0a",
    "alembic",
    "repoze.who == 1.0.19",
#    "repoze.who-testutil",
#    "repoze.who.plugins.sa",
    "repoze.who-friendlyform >= 1.0.4",
    "repoze.what >= 1.0.8",
    "repoze.what-pylons >= 1.0",
    "repoze.what-quickstart",
    "repoze.what.plugins.sql >= 1.0.1",
    "tw2.core >= 2.1.3",
    "tw2.forms >= 2.1.1",
    "tw2.dynforms",
    "tw2.jquery",
    "tw2.bootstrap.forms",
    "tw2.tinymce > 2.0.b4",
    "tw2.jqplugins.chosen",
    "tw2.ace",
    "tgext.admin >= 0.5.3",
    "tgext.crud >= 0.5.6",
    "sprox >= 0.8",  # Dynamic form widget generation
#    "tablesorter >= 0.2",  # JS-sortable TableBase
#    "ipython == 0.10.2",  # For paster shell, install by hand if necessary
    "Pygments",  # For syntax highlighting
    "docutils",  # For rendering documentation
    "chardet",  # For submission file charset detection
    "pygmentize > 0.2",  # Using ToscaWidgets with a SyntaxHighlighting widget
    "numpy", "matplotlib", "libripoff >= 0.2",  # For similarity calculation
    "WebOb == 1.0.8", "Pylons == 1.0", "tg.devtools == 2.1.5",  # To allow one-step installing
    "bootalchemy >= 0.4.1",
    ]

if sys.version_info[:2] == (2, 4):
    print 'WARNING: Your Python version ' + sys.version_info + ' is neither tested nor supported!'
    testpkgs.extend(['hashlib', 'pysqlite'])
    install_requires.extend(['hashlib', 'pysqlite'])
elif sys.version_info[:2] not in ((2, 6), (2, 7)):
    print 'WARNING: SAUCE is not heavily tested under this Python version!'

setup(
    name='SAUCE',
    version='1.3',
    description='System for AUtomated Code Evaluation',
    long_description=open('README.rst').read(),
    author='Moritz Schlarb',
    author_email='sauce@moritz-schlarb.de',
    url='https://github.com/moschlar/SAUCE',
    license='AGPL-3.0',
    setup_requires=["PasteScript >= 1.7"],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2', 'tg.devtools'],
    packages=find_packages(exclude=['ez_setup']),
    install_requires=install_requires,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=testpkgs,
    package_data={'sauce': ['i18n/*/LC_MESSAGES/*.mo',
                            'templates/*/*',
                            'public/*/*']},
    message_extractors={'sauce': [('**.py', 'python', None),
                                  ('templates/**.mako', 'mako', None),
                                  ('public/**', 'ignore', None)]},
    entry_points="""
    [paste.app_factory]
    main = sauce.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
    dependency_links=[
        "http://tg.gy/215/",
        "https://github.com/moschlar/tw2.ace/archive/master.tar.gz#egg=tw2.ace-0.1dev",
        "https://bitbucket.org/percious/bootalchemy/get/0.4.1.tar.gz#egg=bootalchemy-0.4.1",
        "https://github.com/moschlar/SAUCE/downloads",
        ],
    zip_safe=False
)
