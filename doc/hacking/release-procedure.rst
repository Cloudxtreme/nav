=========================================
Checklist for releasing a new NAV version
=========================================

.. highlight:: sh

CI status check
---------------

* Verify that the `stable` jobs in Hudson, at
  https://ci.nav.uninett.no/ , are all green.
* If any tests are failing, these must be resolved before moving forward.


Review milestone for next release in Launchpad
----------------------------------------------

* Check the list of bugs targeted to the upcoming milestone at
  https://launchpad.net/nav .
* Do all the targeted bugs have a status of `Fix Committed`?
* Unless any unfixed bugs are showstoppers, untarget them from this milestone
  to remove clutter.

Getting the code
----------------

* Start by cloning the official stable branch (or use `hg pull` to update your
  existing clone)::

    hg clone https://nav.uninett.no/hg/stable
    cd stable
    hg up tip

* Verify that the current checkout is on the named branch for the currently
  supported stable release, it should be named according to the M.N.x pattern,
  e.g. `3.11.x` for the 3.11 series::

    hg branch

Updating changelog and release notes
------------------------------------

* Generate a list of referenced bugfixes from the changelog since the last
  release::

    hg log -v -r <LASTRELEASE>:tip | ./tools/buglog.py

* Add a new entry to the CHANGES file for for the new release and paste the
  list produced by the above command.

* Verify that all the bugs in this list are in the list of bugs targeted to
  the Launchpad milestone, and vice versa.  Any differences need to be
  resolved manually.

* Once the CHANGES file has been properly updated, commit it, tag the new
  release and push changes back to the official repository::

    hg commit -m 'Update changelog for the upcoming X.Y.Z release'
    hg tag X.Y.Z
    hg push


Rolling and uploading a new distribution tarball
------------------------------------------------

* Update to the newly created tag and create a distribution tarball::

    hg up X.Y.Z
    ./dist.sh -r X.Y.Z

* Create a detached PGP signature of the created tarball::

    gpg --armor --detach-sign nav-X.Y.X.tar.gz

* Browse the Launchpad milestone page and create a new release from the
  milestone.
* Upload the tarball and the detached signature to the release page.
* Set the `Fix Released` status on all bug reports targeted to the new
  release.

Announcing the release
----------------------

* Update the NAV wiki with new version numbers:

  - on the front page
  - on the `Downloads` page

* Change the topic of the #nav freenode IRC channel to reference the new
  release + Launchpad URL.

* Send email announcement to nav-users. Use previous release announcements as
  your template.
