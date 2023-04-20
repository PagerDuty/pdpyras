Advanced Topics
---------------

Logging
*******
When a session is created, a
`Logger object <https://docs.python.org/3/library/logging.html#logger-objects>`_
is created as follows:

* Its level is unconfigured (``logging.NOTSET``) which causes it to defer to the 
  level of the parent logger. The parent is the root logger unless specified
  otherwise (see `Logging Levels
  <https://docs.python.org/3/library/logging.html#logging-levels>`_).
* The logger is initially not configured with any handlers. Configuring
  handlers is left to the discretion of the implementer (see `logging.handlers
  <https://docs.python.org/3/library/logging.handlers.html>`_)
* The logger can be accessed and set through the property
  :attr:`pdpyras.PDSession.log`.

In v5.0.0 and later, the attribute :attr:`pdpyras.PDSession.print_debug` was
introduced to enable sending debug-level log messages from the client to
command line output. It is used as follows:

.. code-block:: python

    # Method 1: keyword argument, when constructing a new session:
    session = pdpyras.APISession(api_key, debug=True)

    # Method 2: on an existing session, by setting the property:
    session.print_debug = True

    # to disable:
    session.print_debug = False

What this does is assign a `logging.StreamHandler
<https://docs.python.org/3/library/logging.handlers.html#streamhandler>`_
directly to the session's logger and set the log level to ``logging.DEBUG``.
All log messages are then sent directly to ``sys.stderr``. The default value
for all sessions is ``False``, and it is recommended to keep it that way in
production systems.

Using a Proxy Server
********************
To configure the client to use a host as a proxy for HTTPS traffic, update the
``proxies`` attribute:

.. code-block:: python

    # Host 10.42.187.3 port 4012 protocol https:
    session.proxies.update({'https': '10.42.187.3:4012'})


HTTP Retry Configuration
************************
Session objects support retrying API requests if they receive a non-success
response or if they encounter a network error. This behavior is configurable
through the following properties:
implementation details:

* :attr:`pdpyras.PDSession.max_http_attempts`
* :attr:`pdpyras.PDSession.max_network_attempts`
* :attr:`pdpyras.PDSession.sleep_timer`
* :attr:`pdpyras.PDSession.sleep_timer_base`
* :attr:`pdpyras.PDSession.stagger_cooldown`

Exponential Cooldown
++++++++++++++++++++
After each unsuccessful attempt, the client will sleep for a short period that
increases exponentially with each retry.

Let:

* a = :attr:`pdpyras.PDSession.sleep_timer_base`
* t\ :sub:`0` = ``sleep_timer``
* t\ :sub:`n` = Sleep time after n attempts
* ρ = :attr:`pdpyras.PDSession.stagger_cooldown``
* r = a random real number between 0 and 1, generated once per request


Assuming ρ = 0:

t\ :sub:`n` = t\ :sub:`0` a\ :sup:`n`

If ρ is nonzero:

t\ :sub:`n` = a (1 + ρ r) t\ :sub:`n-1`

Rate Limiting
+++++++++++++
By default, after receiving a status 429 response, sessions will retry the
request indefinitely until it receives a status other than 429, and this
behavior cannot be overridden. This is a sane approach; if it is ever
responding with 429, the REST API is receiving (for the given REST API key) too
many requests, and the issue should by nature be transient unless there is a
rogue process using the same API key and saturating its rate limit.

It has been considered to make this also configurable so that processes won't
hang indefinitely in the event of persistent rate limit saturation. If you have
a use case where this would help and/or believe it would be generally useful,
please `file an issue <https://github.com/PagerDuty/pdpyras/issues/new>`_.

Setting the retry property
++++++++++++++++++++++++++
The property :attr:`pdpyras.PDSession.retry` allows customization of HTTP retry
logic. The client can be made to retry on other statuses (i.e.  502/400), up to
a set number of times. The total number of HTTP error responses that the client
will tolerate before returning the response object is defined in
:attr:`pdpyras.PDSession.max_http_attempts`, and this will supersede the
maximum number of retries defined in :attr:`pdpyras.PDSession.retry` if it is
lower.

**Example:**

.. code-block:: python

    # This will take about 30 seconds plus API request time, carrying out four
    # attempts with 2, 4, 8 and 16 second pauses between them, before finally
    # returning the status 404 response object for the user that doesn't exist:
    session.max_http_attempts = 4 # lower value takes effect
    session.retry[404] = 5 # this won't take effect
    session.sleep_timer = 1
    session.sleep_timer_base = 2
    response = session.get('/users/PNOEXST')

    # Same as the above, but with the per-status limit taking precedence, so
    # the total wait time is 62 seconds:
    session.max_http_attempts = 6
    response = session.get('/users/PNOEXST')

