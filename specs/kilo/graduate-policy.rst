=================
Graduating Policy
=================


`bp graduate-policy <https://blueprints.launchpad.net/oslo-incubator/+spec/graduate-policy>`_

Graduate the policy API to a standalone library.

The policy code is security sensitive and needs to be managed as a library. If
there is a CVE level defect, deploying a fix should require deploying a new
version of the library, not syncing each individual project.

Library Name
============

The new library will be called `oslo.policy`.

Contents
========

- openstack/common/policy.py
- tests/unit/test_policy.py
- tests/var/policy.d
- tests/var/policy.2.d
- tests/var/policy.json

Early Adopters
==============

- Keystone

Public API
==========

.. code-block:: python

  from oslo_policy import policy

All of the existing public functions and classes will remain public.

.. code-block:: python

    class Rules(dict):
        """A store for rules. Handles the default_rule setting directly."""

    class Enforcer(object):
        """Responsible for loading and enforcing rules.

        :param policy_file: Custom policy file to use, if none is
                            specified, `CONF.policy_file` will be
                            used.
        :param rules: Default dictionary / Rules to use. It will be
                    considered just in the first instantiation. If
                    `load_rules(True)`, `clear()` or `set_rules(True)`
                    is called this will be overwritten.
        :param default_rule: Default rule to use, CONF.default_rule will
                            be used if none is specified.
        :param use_conf: Whether to load rules from cache or config file.
        :param overwrite: Whether to overwrite existing rules when reload rules
                        from config file.
        """

The Rules class has a method to load the rules, currently only via a json file:

.. code-block:: python

    def load_json(cls, data, default_rule=None):
        """Allow loading of JSON rule data."""

The Enforcer class handles rules and the enforcement action, which are
performed by the following public methods:

.. code-block:: python

    def set_rules(self, rules, overwrite=True, use_conf=False):
        """Create a new Rules object based on the provided dict of rules.

        :param rules: New rules to use. It should be an instance of dict.
        :param overwrite: Whether to overwrite current rules or update them
                          with the new rules.
        :param use_conf: Whether to reload rules from cache or config file.
        """

    def clear(self):
        """Clears Enforcer rules, policy's cache and policy's path."""

    def load_rules(self, force_reload=False):
        """Loads policy_path's rules.

        Policy file is cached and will be reloaded if modified.

        :param force_reload: Whether to reload rules from config file.
        """

    def enforce(self, rule, target, creds, do_raise=False,
                exc=None, *args, **kwargs):
        """Checks authorization of a rule against the target and credentials.

        :param rule: A string or BaseCheck instance specifying the rule
                    to evaluate.
        :param target: As much information about the object being operated
                    on as possible, as a dictionary.
        :param creds: As much information about the user performing the
                    action as possible, as a dictionary.
        :param do_raise: Whether to raise an exception or not if check
                        fails.
        :param exc: Class of the exception to raise if the check fails.
                    Any remaining arguments passed to enforce() (both
                    positional and keyword arguments) will be passed to
                    the exception class. If not specified, PolicyNotAuthorized
                    will be used.

        :return: Returns False if the policy does not allow the action and
                exc is not provided; otherwise, returns a value that
                evaluates to True.  Note: for rules using the "case"
                expression, this True value will be the specified string
                from the expression.
        """

A basic check class along with some default extensions: FalseCheck, TrueCheck,
Check, NotCheck, AndCheck, OrCheck, RoleCheck, HttpCheck and GenericCheck. This
checks are used to validate the rules.

.. code-block:: python

    class BaseCheck(object):
        """Abstract base class for Check classes."""


Implementation
==============

Assignee(s)
-----------


Primary assignee:
  Adam Young  ayoung ayoung@redhat.com

Other contributors:
  Rodrigo Duarte rodrigodsousa rodrigods@lsd.ufcg.edu.br


Primary Maintainer
------------------

Primary Maintainer:
  Unknown

Other Contributors:
  None

Security Contact
----------------

Security Contact:
  ayoung

Milestones
----------

kilo-2

Work Items
----------

* The work items are outlined in the `oslo graduation tutorial. <https://wiki.openstack.org/wiki/Oslo/CreatingANewLibrary#Graduating_a_Library_from_the_Incubator>`_
* The public repository, with the code extracted from the incubation module
  can be found `here <https://github.com/rodrigods/oslo.policy>`_.

Adoption Notes
==============

Once released, projects using oslo.policy should change the way policy.py is
being imported to use the `oslo_policy` module instead of the current
`<project>.openstack.common`. Also, they will need to add the lib as
requirements (add to requirements.txt and/or test-requirements.txt files).

Documentation Impact
====================

Library will require its own documentation, but that will be done post
graduation.

Dependencies
============

None

References
==========

* `Oslo Graduation Schedule <https://etherpad.openstack.org/p/kilo-oslo-library-proposals>`_


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
