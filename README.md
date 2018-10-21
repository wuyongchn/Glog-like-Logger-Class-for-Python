# Glog-like Logger Class for Python
===============

This class attempts to create a logger class like Google logging in Python applications.

Behaviours
----------

-  Messages are always written to stderr.

-  Lines are prefixed with a google-style log prefix, for example:

``E0924 22:19:15.123456 19552 filename.py:87] Log message...``

Splitting on spaces, the fields are:

1. The first character is the log level, followed by MMDD (month, day)
2. HH:MM:SS.microseconds
3. Process ID
4. basename\_of\_sourcefile.py:linenumber]
5. The body of the log message.

Example use
-----------

.. code:: python

    from logger import log

    log.set_level("INFO")  # Integer levels are also allowed.
    # by default, log is set to "INFO".
    log.info("It works.")
    log.warning("Something not ideal")
    log.error("Something went wrong")
    log.fatal("AAAAAAAAAAAAAAA!")
    
    # Glog-like check function
    check(condition)
    a = 1
    check(type(a), float)
    check_eq(obj1, obj2)
    check_ne(obj1, obj2)
    check_le(obj1, obj2)
    check_ge(obj1, obj2)
    check_lt(obj1, obj2)
    check_gt(obj1, obj2)
