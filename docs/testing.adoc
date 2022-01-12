= Testing changes

This document explains how to test changes to the frontend, CI, and rspec-tools.

Refer to the <<../README.adoc#AddModifyRule,main documentation>> if you want to modify rules.

== Testing the frontend

If your changes are small and noncontroversial, you can directly create a branch in this repository.

However, when you need to show reviewers how the website will look with your changes,
you can use a fork with your own GitHub Pages.
See <<forking>> for more details.

To test your changes locally, you can start a local HTTP server, such as ``npm start``.
Refer to the frontend documentation for more details.

== Testing the rspec-tools

Modifications to the rspec-tools do not require any special process.
You can therefore use a regular PR from a branch in this repository.

== Testing GitHub Actions

There are two strategies to test GitHub Actions: either use your own branch in this repository, or create a fork.

Choose the solution your need based on the impact your changes can have.
For example, if the changes may spam/modify other Pull Requests, it is wiser to use your own fork.

Note that GitHub will pick the workflow definitions from your branch whether it is in a fork or not.
It will also run new workflow scripts automatically (i.e. there is no configuration to change on GitHub).
When working on a new workflow or updating existing ones, since it may confuse other people to see unexpected results,
it is preferable to use your own fork while iterating on your work.

See <<forking>> for more details.

== Testing Cirrus CI

To test modification to the Cirrus CI script, you need to create your own branch in this repository (not a fork).
Cirrus CI will automatically pick up the version of the scripts on that branch.

[[forking]]
== Forking

Forking this repository is fairly trivial.

. Click "Fork" on the top right and select your own account.

. If needed, enable GitHub Actions:
.. in your fork, go to the "Actions" page,
.. click on the green button to enable workflows,
.. and, if needed, additionally enable the "Update rule coverage" workflow,
   which is disabled by default because it executes on a schedule.

. If needed, enable GitHub Pages:
.. enable the GitHub Actions so that the ``gh-pages`` branch is properly populated,
.. go to "Settings" > "Pages" and under "Source"
*** set "Branch" to "gh-pages",
*** select "/ (root)" as the source folder,
*** and click "save".

If you need to rely on GitHub Actions, you can work on your fork's ``master`` branch to ensure that
the "Build and Deploy" workflow gets triggered out of the box.

Once you are done with your feature and your PR was merged, you can delete your fork.
If you prefer to keep the fork alive, don't forget to merge the upstream changes before working on your next feature.
