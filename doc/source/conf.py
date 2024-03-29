# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import sys
import warnings

# Try to only emit warnings about SSL issues one time.
try:
    from requests.packages.urllib3 import exceptions
    warnings.filterwarnings('ignore', '.*',
                            exceptions.InsecurePlatformWarning)
    warnings.filterwarnings('ignore', '.*',
                            exceptions.SNIMissingWarning)
except ImportError:
    pass

sys.path.insert(0, os.path.abspath('../..'))
# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'openstackdocstheme',
    'yasfb',
]

openstackdocs_repo_name = 'openstack/oslo-specs'
openstackdocs_auto_version = False

version = ''
release = ''

# Feed configuration for yasfb
feed_base_url = 'https://specs.openstack.org/openstack/oslo-specs'
feed_author = 'OpenStack Oslo Team'

# Optionally allow the use of sphinxcontrib.spelling to verify the
# spelling of the documents.
try:
    import sphinxcontrib.spelling
    extensions.append('sphinxcontrib.spelling')
except ImportError:
    pass

exclude_patterns = [
    '**/graduation-template.rst',
    '**/new-library-template.rst',
    '**/template.rst',
    '**/policy-template.rst',
]

# autodoc generation is a bit aggressive and a nuisance when doing heavy
# text edit cycles.
# execute "export SPHINX_DEBUG=1" in your terminal to disable

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'oslo-specs'
copyright = '%s, OpenStack Foundation' % datetime.date.today().year

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme_path = ["."]
# html_theme = '_theme'
# html_static_path = ['static']
html_theme = 'openstackdocs'

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    ('index',
     '%s.tex' % project,
     '%s Documentation' % project,
     'OpenStack Foundation', 'manual'),
]

# Example configuration for intersphinx: refer to the Python standard library.
#intersphinx_mapping = {'http://docs.python.org/': None}
