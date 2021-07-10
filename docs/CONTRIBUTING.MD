Before starting work on a new feature/bug fix create an Issue in our GitHub repository and describe
what you are planning to do or what the issue is about. There we can discuss if what you are proposing is something we would like to
add and what the best way to do that is.

___

## Issue approval process

When you create an issue it will automatically be labeled with `stage 1`.
This means that the proposed features need to be reviewed and discussed.
If the issue looks promising it will be labeled with `stage 2`.
In this stage we discuss the best way to design the proposed features with the issue author and
the issue is moved to the `In discussion` column in the repos project.
If we come to an agreement the issue will be labeled with `approved`.
Issues labeled `approved` will be worked on and eventually implemented. These issues will also be moved to `In progress`
column in the repos project.

In both `stage 1` and `stage 2` the issue can be labeled with `wont implement`. This means that this particular
issue will not be worked on at the moment. This can happen because of various reasons - disagreements, library restrictions,
etc

## Code approval process
* File a Pull Request with a number of well-defined clearly described commits
(following what is described in [this article](https://chris.beams.io/posts/git-commit) is a good start).
* Multiple commits per PR are allowed, but please do not include revert commits, etc. Use rebase.
* Make sure that the code is well formatted - use `Black` for that.
* Assign [Kobu](https://github.com/Kobu) or any other bot maintainer as reviewer.
* When addressing code review comments please use fixup commits
* After the PR is approved, use git rebase -i [PARENT_BRANCH] --autosquash. This will squash the fixup commits.
* One of the reviewers will merge the PR.

