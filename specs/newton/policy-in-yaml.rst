==============================
 Support policy files in YAML
==============================

https://blueprints.launchpad.net/oslo?searchtext=policy-yaml

JSON is great for a wire format, but awful for a configuration file.
oslo.policy can easily also support a safe subset of YAML.

Problem description
===================

The policy files for the services can be complicated and hard to use. Even
knowing what operations are protected by what rules is difficult since the
operation name (e.g., ``identity:create_user``) isn't the same as the
operation the user performs (e.g., ``PUT /v3/users``). The sample policy files
would be a lot more usable if we could simply put a comment in the file saying
what the user operation is for the rule, but the only format allowed (JSON)
doesn't support comments.

Use Cases
---------

As a deployer, I should be able to comment the policy file with descriptions
for my custom roles and rules.

As a developer, I should be able to provide a sample policy file that's
self-describing. As in, add comments to the sample policy file.


Proposed change
===============

Rather than parse the policy file using the JSON parser, oslo.policy will
parse it using the YAML parser (provided by PyYAML). Since JSON is a subset of
YAML existing JSON files will continue to work. Projects and deployers can
switch to simplified YAML and document using comments if they want.

`oslo.policy` will be changed to use PyYAML's `safe_load()` to parse the
policy file rather than the JSON parser ( `jsonutils.loads()` ).

For some reason the name of the method to read the policy file includes the
format. This was incorrect to begin with and is made even less accurate since
the format is YAML, so rename `load_json()` to `load()` (keeping the old
method name around but deprecated, using debtcollector).

oslo.policy defines a `policy_file` config option which defaults to
``policy.json``. So the default behavior is to look for a ``policy.json``
file. The new default behavior will look first for ``policy.yaml`` and if that
doesn't exist it will look for ``policy.json``. As such, the default will be
removed and the new default behavior will be described in the help text.

Files to change:

* oslo_policy/policy.py
* oslo_policy/opts.py
* requirements.txt

Alternatives
------------

We could preprocess the JSON files to remove lines that look like comments.
But then the format isn't really JSON and is not a standard format.

We could have separate loaders for JSON vs YAML and use the parser based on
the file extension. This is possible but is unnecessary since JSON is a subset
of YAML.

Impact on Existing APIs
-----------------------

The `oslo_policy.policy.Rules` class's `load_json` method will be renamed to
`load`. `load_json` will be deprecated.

Security impact
---------------

In its most general form, YAML allows the document to contain executable code
that's then run. We don't want our policy files to be allowed to contain
executable code. As such, we'll use `safe_load()` instead of `load()`.

See http://pyyaml.org/wiki/PyYAMLDocumentation#LoadingYAML

Performance Impact
------------------

I don't know if the YAML parser is a lot slower, but since it supports several
representations for the same result I assume it takes more work to parse it.
The policy file is read when the server starts and also whenever the file
changes (it used to be read on every request, but that's been changed to check
the modification time), so I don't think this is going to be noticable.

Configuration Impact
--------------------

None.

Developer Impact
----------------

The different projects all have sample policy.json files. These files should
be renamed to policy.yaml, the format changed to simplified YAML, and comments
added. This doesn't have to happen immediately since policy.json will continue
to work.

Testing Impact
--------------

The projects are already loading their policy files during gate testing.

Implementation
==============

Assignee(s)
-----------
Primary assignee:
  blk-u

Milestones
----------

Target Milestone for completion:
  newton-1

Work Items
----------

* Change oslo.policy to use yaml.safe_load() rather than json.loads()
* Rename oslo_policy.policy.Rules load_json() to load(), use debtcollector
  to rename.
* Change oslo.policy to look for ``policy.yaml`` first and then look for
  ``policy.json``. `policy_dirs` will also use this.
* References to JSON need to be changed to YAML in general:
  ** `policy_file` help text.

Incubation
==========

N/A

Adoption
--------

N/A

Library
-------

N/A

Anticipated API Stabilization
-----------------------------

N/A

Documentation Impact
====================

If the documentation mentions that the policy file is in JSON format then that
can be changed to say YAML format. Any policy sample files should be changed
to the simpler YAML format rather than JSON.

Dependencies
============

oslo.policy will depend on PyYAML. This is already in global-requirements.

References
==========

debtcollector: http://docs.openstack.org/developer/debtcollector/

JSON: http://www.json.org/

oslo.policy: http://git.openstack.org/cgit/openstack/oslo.policy/
  http://docs.openstack.org/developer/oslo.policy/

PyYAML: http://pyyaml.org/

YAML: http://yaml.org/


.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode
