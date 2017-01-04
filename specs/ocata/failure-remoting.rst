===========================================
 Unifying and cleaning up failure remoting
===========================================

https://blueprints.launchpad.net/oslo.messaging/+spec/failure-remoting

We currently have a couple ways of remoting failures (exceptions +
traceback information) that occur on remote systems back to their
source. These different ways have differences that make each solution
valid and applicable to its problem area. To encourage unification, this
spec will work on a proposal that can take the best aspects of both
implementations and leave the weaknesses of both behind to make a
best of breed implementation.

Problem description
===================

There is a repeated desire to be able to serialize an exception, an
exception type, and as much information about the exceptions cause (ie
its traceback) when a creator on a remote system fails to some
other system (typically transmitted over some RPC or REST or other
non-local interface). For brevity sake let us call the tuple
of ``(exception_type, value, traceback)`` (typically created from some
call to `sys.exc_info`_) a **failure** object. When on a local machine
and the failure is created inside its own process the exception, its class
and its traceback are natively supported and can be examined, output,
logged (typically using the `traceback`_ module), handled (via ``try/catch``
blocks) and analyzed; but when that exception is remotely created and
sent to a receiver the recreation of that failure becomes that much more
complicated for a few reasons:

* Serialization of a traceback object (which typically contains references
  to local stack frames) into some serializable format typically means that
  the reconstructed traceback will not be as *rich* as it was when created
  on the local process due to the fact that those local stack frames
  will *not* exist in the receivers process. This implies that traceback
  serialization/deserialization is a lossy process and by side-effect
  this means that for remote exceptions the `traceback`_ module
  can *not* be used and/or that the information it produces may
  not be accurate.
* Input validation must now be performed, ensuring that the serialized format
  created by the sender is actually valid (this excludes using `pickle`_
  for serialization/deserialization due to its widely known security
  vulnerabilities).
* The receiver of the failure, if it desires to *try* to recreate an
  exception object from the serialized version **must** have access to the
  same exception type/class that was used to create the original
  exception; this may not always be possible (depending on modules and classes
  accessible from the receivers ``sys.path``).
* Any contained exception value (typically a ``string``, but not limited to)
  will need to be reconstructed (this may not always be possible, for
  example if the originating exception value references some local file
  handle or other non-serializable object, such as a local threading lock).

.. _sys.exc_info: https://docs.python.org/2/library/sys.html#sys.exc_info
.. _pickle: https://docs.python.org/2/library/pickle.html
.. _traceback: https://docs.python.org/2/library/traceback.html

What exists
===========

There are a few known implementations of failure capturing, serialization
and deserialization/reconstruction. Let us dive into how each one works and
analyze the benefits and drawbacks of each approach.

Oslo.privsep
------------

Source:

* https://github.com/openstack/oslo.privsep/blob/1.13.0/oslo_privsep/daemon.py#L181-L187
* https://github.com/openstack/oslo.privsep/blob/1.13.0/oslo_privsep/daemon.py#L181-L187

Commentary
~~~~~~~~~~

* Sends back class + module name across socket channel + exception arguments.
* Drops traceback (logs it on priviliged side).
* Recreates new class object with sent across arguments (and reraises)
  on unpriviliged side (ideally nothing leaks across?).

Oslo.messaging
--------------

Source:

* https://github.com/openstack/oslo.messaging/blob/2.5.0/oslo_messaging/_drivers/common.py#L164
* https://github.com/openstack/oslo.messaging/blob/2.5.0/oslo_messaging/_drivers/common.py#L204

A similar (same?) copy seems to be in nova (for cells?):

* https://github.com/openstack/nova/blob/stable/liberty/nova/cells/messaging.py#L1878
* https://github.com/openstack/nova/blob/stable/liberty/nova/cells/messaging.py#L1918

Docs: unknown

Commentary
~~~~~~~~~~

Serializes: yes (to json); keyword arguments of exception are extracted
from optional exception attribute ``kwargs``, class name and module name
of exception are captured with final data format being::

    data = {
        'class': cls_name,
        'module': mod_name,
        'message': six.text_type(exception),
        'tb': tb,
        'args': exception.args,
        'kwargs': kwargs
    }

Deserializes: yes; previous json data is loaded as a dictionary.

Validates: No; `jsonschema`_ validation is not currently performed.

Reconstructs: yes (with limitations);  message of exception from
``message`` in ``data`` is loaded and concated with traceback from ``tb``
dictionary element, module received is then verified against a provided list
and if module received is not allowed a generic exception is raised which
attempts to encapsulate the received failure. This generic
exception (which does retain the traceback) is created via::

    oslo_messaging.RemoteError(data.get('class'), data.get('message'),
                               data.get('tb'))

Otherwise if the module is one of the allowed types the exception class
object is recreated by using::

    klass = <load module and class and verify class is an exception type>
    exception = klass(*data.get('args', []), **data.get('kwargs', {}))

Then if this works, to ensure the ``__str__`` and ``__unicode__`` methods
correctly return the ``message`` key in the previously mentioned ``data``
dictionary a dynamic exception type is created with a dynamically created
function that returns provided ``message``; then the ``exception`` created
above has its ``__class__`` attribute replaced to be this new dynamic
exception type (woah!)::

    exc_type = type(exception)
    str_override = lambda self: message
    new_ex_type = type(ex_type.__name__ + _REMOTE_POSTFIX, (ex_type,),
                       {'__str__': str_override, '__unicode__': str_override})
    new_ex_type.__module__ = '%s%s' % (module, _REMOTE_POSTFIX)
    exception.__class__ = new_ex_type

if this doesn't work then ``exception`` is returned
untouched and instead the ``exception.args`` list is replaced with a new
``args`` list that has the ``message`` from the ``data`` dict as its first
entry (replacing the prior ``args`` first entry with its own).

Notes:

* Appears to lose remote traceback info during above reconstruction
  process (unless `RemoteError`_ is returned, which does not
  lose the traceback, but does lose the original type + associated
  information).
* Does not capture `chained`_ exception information.
* Copied (or some version of it) into nova cells (currently unknown what
  version/sha the nova folks copied from).

.. _RemoteError: http://docs.openstack.org/developer/\
                 oslo.messaging/rpcclient.html#oslo_messaging.RemoteError

TaskFlow
--------

Source:

* https://github.com/openstack/taskflow/blob/1.21.0/taskflow/types/failure.py

Docs:

* http://docs.openstack.org/developer/taskflow/types.html#module-taskflow.types.failure

Commentary
~~~~~~~~~~

Serializes: True; translates exception (or ``sys.exc_info`` call) into
a dictionary using ``to_dict`` method. Example::

    >>> from taskflow.types import failure
    >>> try:
    ...    raise IOError("I have broke")
    ... except Exception:
    ...    f = failure.Failure()
    ...
    >>> print(json.dumps(f.to_dict(), indent=4, sort_keys=True))
    {
        "causes": [],
        "exc_type_names": [
            "IOError",
            "EnvironmentError",
            "StandardError",
            "Exception"
        ],
        "exception_str": "I have broke",
        "traceback_str": "  File \"<stdin>\", line 2, in <module>\n",
        "version": 1
    }

Deserializes: True; loads from json into dictionary.

Validates: True; uses `jsonschema`_ with schema::

    SCHEMA = {
        "$ref": "#/definitions/cause",
        "definitions": {
            "cause": {
                "type": "object",
                'properties': {
                    'version': {
                        "type": "integer",
                        "minimum": 0,
                    },
                    'exception_str': {
                        "type": "string",
                    },
                    'traceback_str': {
                        "type": "string",
                    },
                    'exc_type_names': {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "minItems": 1,
                    },
                    'causes': {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/cause",
                        },
                    }
                },
                "required": [
                    "exception_str",
                    'traceback_str',
                    'exc_type_names',
                ],
                "additionalProperties": True,
            },
        },
    }

Reconstructs: True when failure objects are raised locally (when serialization
is not used). False when serialized using ``to_dict``; Instead of going
through process like defined in ``oslo.messaging`` above this object
instead wraps originating exception(s) in a new exception `WrappedFailure`_ and
exposes its type (string version of) information and its traceback in a
new exception and provides accessors and useful methods (defined on the
failure class) to contained information for introspection purposes.

Notes:

* Captures (and serializes and deserializes) `chained`_ exceptions (as
  nested failure objects). Seen in above schema as ``causes`` key (which
  self-references the schema object).

.. _chained: https://www.python.org/dev/peps/pep-3134/
.. _WrappedFailure: http://docs.openstack.org/developer/\
                    taskflow/exceptions.html#taskflow.exceptions.WrappedFailure
.. _jsonschema: http://json-schema.org/

Twisted
-------

Source:

* https://github.com/twisted/twisted/blob/twisted-15.4.0/twisted/python/failure.py

Docs:

* http://twistedmatrix.com/documents/current/api/twisted.python.failure.html

Commentary
~~~~~~~~~~

Example::

    >>> from twisted.python import failure
    >>> import pickle
    >>> import traceback
    >>> def blow_up():
    ...    raise ValueError("broken")
    >>> try:
    ...    blow_up()
    ... except ValueError:
    ...    f = failure.Failure()
    >>> print(f)
    [Failure instance: Traceback: <type 'exceptions.ValueError'>: broken
    --- <exception caught here> ---
    <stdin>:2:<module>
    <stdin>:2:blow_up
    ]
    >>> f.raiseException()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 2, in <module>
      File "<stdin>", line 2, in blow_up
    ValueError: broken
    >>> f_p = pickle.dumps(f)
    >>> f_2 = pickle.loads(f_p)
    >>> f_2.raiseException()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<string>", line 2, in raiseException
    ValueError: broken
    >>> print(f_2.tb)
    None
    >>> traceback.print_tb(f_2.getTracebackObject())
      File "<stdin>", line 2, in <module>
      File "<stdin>", line 2, in blow_up

Serializes: `pickle`_ supported via ``__getstate__`` method. Since
they have created a *mostly* working replacement for the frame information
that a traceback stores it becomes possible to better integrate with
the `traceback`_ module (which accesses that frame information to try to
create useful traceback details).

Deserializes: Yes, via `pickle`_.

Validates: No (`pickle`_ is known to be vulnerable anyway to loading
arbitrary code).

Reconstructs: Partially, a frame-like replica structure is created that
*mostly* works like the original (except it can't be re-raised, but it
can be passed to the `traceback`_ module to have its functions seemingly
work).

Proposed change
===============

Create a new library, https://pypi.python.org/pypi/failure (or other better
named library) that encompasses the combination of the 3-4 models described
above.

It would primarily provide a ``Failure`` object (like provided by
taskflow and twisted) as its main exposed API. That failure
class would have a ``__get_state__`` method so that it can be pickled (for
situations where this is desired) and a ``to_dict`` and ``from_dict`` that
can be used for json serialization and deserialization. It would also have
introspection APIs (similar to what is provided by twisted and taskflow) so
that the underlying exception information can be accessed in nice manner.

Basic examples of these API(s) that would be great to have (and have
proven themselves useful)::

    @classmethod
    def validate(cls, data):
        """Validate input data matches expected failure format."""

    def check(self, *exc_classes):
        """Check if any of ``exc_classes`` caused the failure.

        ...

        """

    def reraise(self):
        """Re-raise captured exception."""

    @property
    def causes(self):
        """Tuple of all *inner* failure *causes* of this failure.

        ...

        """

    def pformat(self, traceback=False):
        """Pretty formats the failure object into a string."""

    @classmethod
    def from_dict(cls, data):
        """Converts this from a dictionary to a object."""

    def to_dict(self):
        """Converts this object to a dictionary."""

    def copy(self):
        """Copies this object."""

To take advantage of the re-raising capabilities in oslo.messaging this
class should also have a ``reraise`` method that can attempt to reraise the
given failure (if and only if it matches a given list of exception types). It
would **not** attempt to dynamically create a ``__str__`` and ``__repr__``
method (the class manipulation magic happening in oslo.messaging) to avoid
the peculiarities of this chunk of code. If the contained failure does
not match a known list of failures, then ``reraise`` will return false and
it will not re-raise anything (leaving it up to the caller to decide what
to do in this situation, perhaps at this point a common  `WrappedFailure`_
like exception should be raised?).

The validation logic using `jsonschema`_ would be taken from taskflow and
used when deserializing so that errors with *bad* data can be found
earlier (at data load time) rather than later (at data access time).

To provide the twisted like integration with the traceback module (by
turning the internal format of a traceback into a pure python object
representation) there has been discussed if the `traceback2`_ module can
provide equivalent functionality, if it can then it should be used to
achieve similar integration (it would be even better if the integration
would also allow for re-raising this pure python trackback and frame
representation as an actual traceback, although this may not be a reasonable
expectation).

.. _traceback2: https://pypi.python.org/pypi/traceback2/

Alternatives
------------

Keep having multiple variations, each with their own weaknesses and
benefits, instead of unifying them under a single library.

Impact on Existing APIs
-----------------------

Ideally none, as the users should still get the same functionality, but
if this is done correctly they will get more meaningful tracebacks, more
meaningful introspection on failure objects and overall better and more
consistent failures.

Security impact
---------------

Performance Impact
------------------

N/A

Configuration Impact
--------------------

N/A

Developer Impact
----------------

This should make developers lives better.

Testing Impact
--------------

Having the failure code in its own library, allows it to be easily mocked
and tested (vs say having it deeply embedded in oslo.messaging where it is
not so easily testable/reviewable...); so overall this should improve
test coverage (and overall code quality).

Implementation
==============

Assignee(s)
-----------

Primary assignee: harlowja

Milestones
----------

Target Milestone for completion: Mikita

Work Items
----------

#. Create skeleton library.
#. Get skeleton up on gerrit and integrated into oslo pipelines.
#. Start to move around code from oslo.messaging and taskflow
   and refactor to start to form this new library; use concepts and
   learning from twisted and bolt-ons (and others) to help make this
   library the best it can be.
#. Review and code and repeat.
#. Release and integrate.
#. Delete older dead code.
#. Profit!

Incubation
==========

N/A

Documentation Impact
====================

Dependencies
============

References
==========

N/A (all inline)

.. note::

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

