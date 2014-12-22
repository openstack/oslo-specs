..

========================
 Creating debtcollector
========================

https://blueprints.launchpad.net/oslo.utils/+spec/adopt-debtcollector

The goal of this library would be to provide well documented
*developer facing deprecation* patterns that start of with the a basic set and
can expand into a larger set of patterns as time goes on (it would **not**
start off being a library that would be used for operator facing deprecation,
as that is already covered by the ``versionutils.py`` module in the
oslo-incubator).

For example the following patterns could be considered common:

* Deprecating a keyword argument to be later replaced with a replacement
  keyword argument (useful when a new name was later determined to be better
  than an initial name).
* Altering the name of a property to refer to a new and improved name (useful
  when say a property name is discovered after a certain amount of time to
  make more sense than an initial property name).
* Moving a class (with or without breaking those who are inheriting from
  your old location); this is useful when a class is better located at a
  different (potentially better named, more meaningfully named) module than
  it was initially placed at (this is common when the initial location was
  thought of to be a good location, but after usage a alternative location
  would make more sense).
* ...

The desired output of these patterns would be an application of
the `warnings`_ module that would use the common functions that module provides
to emit ``DeprecationWarning`` or ``PendingDeprecationWarning`` or similar
derivative to developers using libraries (or potentially applications)
about future deprecations.

Since the `warnings`_ module supports different types of actions we should
take advantage of that capability (or extend it as needed) to avoid creating
a bunch of *garbage* messages that will appear for the developers using
deprecated features/functionality.

For example the library/functions provided should be affected by the warnings
modules action strings that are defined/copied below.

=======  ======================================================================
Value    Disposition
=======  ======================================================================
error    turn matching warnings into exceptions
ignore   never print matching warnings (the *default* in python 2.7+)
always   always print matching warnings
default  print the first occurrence of matching warnings for each location
         where the warning is issued
module   print the first occurrence of matching warnings for each module where
         the warning is issued
once     print only the first occurrence of matching warnings, regardless of
         location
=======  ======================================================================

Using these settings appropriately would be expected to help avoid polluting
logs or ``sys.stderr`` where these messages can show up (we should look
into how to make these messages visible in the openstack CI system, and
less/not visible in a released library).

To aid in this process it might be useful to hook into the following (but
this can be for later discussion):

https://docs.python.org/2/library/logging.html#logging.captureWarnings

Depending on future functionality we could let applications use the
``logging.captureWarnings`` function, or provide this in ``oslo.log`` or do
something different (the point being that the `warnings`_ module and supporting
API will be the entrypoint that these patterns use, how applications or other
libraries adapt/plugin to the `warnings`_ module can be adjusted and tweaked
as seen fit).

Library Name
============

*debtcollector*

Contents
========

* ``debtcollector/__init__.py``
* ``debtcollector/utils.py``  (internal utils, not for public usage)
* ``debtcollector/moves.py`` (for patterns common to
  moving code/classes/properties...)
* ``debtcollector/renames.py`` (for patterns common to
  renaming code/classes/properties...)
* ... (others as patterns emerge)

Early Adopters
==============

* Taskflow
* Others?

Public API
==========

Current idea for API (will likely evolve as new patterns appear...)

* ``debtcollector/moves.py``

::

    # Patterns devoted to 'moving' functions, methods, classes, arguments...

    def moved_decorator(kind, new_attribute_name, message=None,
                        version=None, removal_version=None,
                        stacklevel=3)

     # Creates a decorator of the given kind for the given attribute name
     # with the provided message, version deprecated in, the version it will
     # be removed in and the given stacklevel (used to output the users code
     # location when this decorator is called).
     #
     # An example message:
     >>> kind = 'Property'
     >>> new_attribute_name = 'a'
     >>> what = "%s '%s' has moved to '%s" % (kind, 'b', new_attribute_name)
     >>> deprecation._generate_moved_message(what, message='sorry its going away', version='0.1', removal_version='0.2')
     "Property 'a' has moved to 'b' in version '0.1' and will be removed in version '0.2': sorry its going away"

     def moved_property(new_attribute_name, message=None,
                        version=None, removal_version=None, stacklevel=3):

     # Decorator specialization of moved_decorator that sets the kind to
     # a property instead of allowing it to be specified.

     def moved_class(new_class, old_class_name, old_module_name, message=None,
                     version=None, removal_version=None, stacklevel=3):

     # Same as moved_decorator but for classes, returns a class proxy that can
     # not be inherited from (useful for when the user of this is aware that no
     # inheritance is happening)

     def moved_class_inheritable(new_class, old_class_name, old_module_name, message=None,
                                 version=None, removal_version=None, stacklevel=3):

     # Same as moved_class but for classes, returns a new-old class that can
     # be inherited from (useful for when the user of this is unaware if any
     # inheritance is happening)

     ...

* ``debtcollector/renames.py``

::

    # Patterns devoted to 'renaming' functions, methods, classes, arguments...

    def renamed_kwarg(old_name, new_name, message=None,
                      version=None, removal_version=None, stacklevel=3):

    # Creates a decorator that can be applied to a keyword argument accepting
    # method, function, callable that will warn the user of that function
    # when they are using the old, to be removed keyword argument; creates
    # an appropriate message telling the user this (in a similar format
    # as mentioned above).

    ...

* ``debtcollector/utils.py``

::

    # Generic *internal* library used utils...

    def generate_message(prefix, postfix=None, message=None,
                         version=None, removal_version=None):

    # Generates the messages for renames or moves in a common (share as much
    # as possible manner) so that the messages look and feel like they are
    # coming from a common library

    ...

Implementation
==============

Assignee(s)
-----------

Primary assignee:

* Harlowja

Other contributors:

* You?

Primary maintainer
------------------

Primary maintainer:

* Harlowja (@yahoo)

Other contributors:

* Szhukov (@yahoo)
* You?

Security Contact
----------------

Security Contact: harlowja

Milestones
----------

Target Milestone for completion: kilo-2

Work Items
----------

* Change owner of Launchpad project (make it part of the Oslo projectgroup)

  * https://launchpad.net/debtcollector

* Give openstackci Owner permissions on PyPI
* Create Initial Repository
* Make the library do something
* Update the README.rst
* Publish git repo
* Oslo team review new repository
* Infra project configuration
* Update Gerrit Groups and ACLs
* openstack-infra/devstack-gate adjustments
* openstack/requirements projects.txt adjustments
* Update project list on docs.openstack.org
* Tag a release
* Profit!

Adoption Notes
==============

N/A

Dependencies
============

Requirements
------------

* python 2.6 --> 3.4 (and beyond!)
* wrapt (http://wrapt.readthedocs.org)
* six (https://bitbucket.org/gutworth/six)

.. note::

 All of the currently planned dependencies are in the requirements repository.

References
==========

* http://lists.openstack.org/pipermail/openstack-dev/2014-December/052692.html

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

.. _warnings: https://docs.python.org/2/library/warnings.html
