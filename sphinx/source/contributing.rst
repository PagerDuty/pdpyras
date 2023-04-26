==================
Contribution Guide
==================

Bug reports and pull requests to fix issues are always welcome, as are
contributions to the built-in documentation.

If adding features, or making changes, it is recommended to update or add tests
and assertions to the appropriate test case class in ``test_pdpyras.py`` to
ensure code coverage. If the change(s) fix a bug, please add assertions that
reproduce the bug along with code changes themselves, and include the GitHub
issue number in the commit message.

Initial Setup
-------------
To be able to rebuild the documentation and release a new version, first make
sure you have `make <https://www.gnu.org/software/make/>`_ and `pip
<https://pip.pypa.io/en/stable/installation/>`_ installed in your shell
environment.

Next, install Python dependencies for building and publishing as well as
testing locally:

.. code-block:: shell

    pip install -r requirements.txt
    pip install -r requirements-publish.txt 

Running Unit Tests
------------------
Assuming that all dependencies are installed, running ``test_pdpyras.py`` in
the root path of the repository will run the unit test suite:

.. code-block:: shell

    ./test_pdpyras.py


Updating Documentation
----------------------

The ``.rst`` files in ``sphinx/source`` are where most of the documentation
lives. The files ``CHANGELOG.rst`` and ``README.rst`` in the root of the
repository also contain content that is included when the HTML documentation is
built.

To rebuild the HTML documentation from the source, run:

.. code-block:: shell

    make docs

Releasing a New Version
-----------------------

You will first need valid user accounts on both ``pypi.org`` and ``test.pypi.org``
that have the "Maintainer" role on the project, as well as the requirements
installed (see above).

Perform end-to-end publish and installation testing
***************************************************

To test publishing and installing from the package index, first make sure you
have a valid user account on ``test.pypi.org`` that has publisher access to the
project as on ``pypi.org``.

Note, once a release is uploaded, it is no longer possible to upload a release
with the same version number, even if that release is deleted. For that reason,
it is a good idea to first add a suffix, i.e. ``-dev001``, to ``__version__``
in ``setup.py``.

To perform end-to-end tests, run the following, entering credentials for
``test.pypi.org`` when prompted:

.. code-block:: shell

    make testpublish

The make target ``testpublish`` performs the following:

* Build the Python egg in ``dist/``
* Upload the new library to ``test.pypi.org``
* Test-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv that does not already have the library installed, to test
  installing for the first time
* Tests-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv where the library is already installed, to test upgrading

If any errors are encountered, the script should immediately exit. Errors
should be investigated and mitigated before publishing. To test again,
temporarily change ``__version__`` so that it counts as a new release
and gets uploaded, and set it to the desired version before the actual
release.

Merge changes and tag
*********************

A pull request for releasing a new version should be created, which along with
the functional changes should also include at least:

* An update to the changelog, where all items corresponding to community
  contributions end with (in parentheses) the GitHub user handle of the
  contributor, a slash, and a link to the pull request (see CHANGELOG.rst for
  preexisting examples).
* A change in the version number in both setup.py and pdpyras.py, to a new
  version that follows `Semantic Versioning <https://semver.org/>`_.
* Rebuilt HTML documentation

The HTML documentation can be rebuilt with the ``docs`` make target:

.. code-block:: shell

    make docs

After rebuilding the documentation, it can then be viewed by opening the file
``docs/index.html`` in a web browser. Including rebuilt documentation helps
reviewers by not requiring them to have the documentation-building tools
installed.

Once the pull request is approved, merge, then checkout main and tag:

.. code-block:: shell

    git checkout main && \
      git pull origin main && \
      git tag "v$(python -c 'from pdpyras import __version__; print(__version__)')" && \
      git push --tags origin main

Publishing
**********

Once the changes are merged and tagged, make sure your local repository clone
has the ``main`` branch checked out at the latest avialable commit, and the
local file tree is clean (has no uncommitted changes). Then run:

.. code-block:: shell

    make publish


