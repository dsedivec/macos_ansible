#!/usr/bin/python

# Copyright: (c) 2018, Dale Sedivec <dale@codefu.org>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: x_git_update

short_description: Clone and update a Git repository

version_added: "2.8"

description:

    - "Not nearly as feature-ful as the built-in git module, this
      module exists to clone a repo and/or make sure it points at the
      right remote, then optionally updating it, trying to preserve a
      dirty working tree."

options: TBD

author:
    - Dale Sedivec (@dsedivec)
"""

EXAMPLES = """TBD"""

RETURN = """TBD"""

# fmt: off

import collections
import os.path
import pathlib
import subprocess

from ansible.module_utils.basic import AnsibleModule

# fmt: on


GitResult = collections.namedtuple("GitResult", "return_code stdout stderr")


def run_git(module, cwd, args, check=(0,)):
    cmd = [module.params["executable"]]
    cmd.extend(args)
    git = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = git.communicate()
    if check and not isinstance(check, collections.Container):
        check = (0,)
    if isinstance(check, collections.Container) and git.returncode not in check:
        module.fail_json(
            msg="Error running %r, stderr: %s" % (" ".join(cmd), stderr)
        )
    return GitResult(git.returncode, stdout.strip(), stderr)


def run_module():
    module_args = dict(
        dest=dict(type="path", required=True),
        remote=dict(type="str", default="origin"),
        repo=dict(type="str", required=True),
        branch=dict(type="str"),
        update=dict(type="bool", default=True),
        update_mode=dict(
            type="str",
            # XXX Are these really mutually exclusive?  Does this even
            # make sense?
            choices=("ff", "ff-only", "no-ff", "rebase", "rebase-autostash"),
            default="ff-only",
        ),
        executable=dict(type="path"),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False, original_message="", message="")

    dest = module.params["dest"]
    remote = module.params["remote"]
    repo = module.params["repo"]
    branch = module.params.get("branch")

    if not module.params.get("executable"):
        module.params["executable"] = module.get_bin_path("git", required=True)

    dest_is_dir = os.path.isdir(dest)
    if dest_is_dir:
        git_result = run_git(module, dest, ["rev-parse", "--is-inside-work-tree"])
        if git_result.stdout != "true":
            module.fail_json(
                msg="%r is not a Git working tree" % (dest,), **result
            )
        result["before"] = run_git(module, dest, ["rev-parse", "HEAD"]).stdout
        git_config = run_git(
            module,
            dest,
            ["config", "--get", "remote.%s.url" % (remote,)],
            check=(0, 1),
        )
        if git_config.return_code == 1:
            # Remote doesn't exist.
            result["changed"] = True
            if not module.check_mode:
                run_git(module, dest, ["remote", "add", remote, repo])
        elif git_config.stdout != repo:
            result["changed"] = True
            if not module.check_mode:
                run_git(module, dest, ["remote", "set-url", remote, repo])
    else:
        result["before"] = None
        result["changed"] = True
        if not module.check_mode:
            parent_dir = pathlib.Path(dest).parent
            run_git(module, parent_dir, ["clone", repo, dest])
            dest_is_dir = True

    if dest_is_dir and branch:
        git_result = run_git(module, ["rev-parse", "--abbrev-ref", "HEAD"])
        if git_result.stdout != branch:
            result["changed"] = True
            if not module.check_mode:
                run_git(module, ["checkout", branch])

    if module.params["update"] and not module.check_mode:
        # XXX should probably support remote ref in this module.
        args = ["pull"]
        if module.params["update_mode"] == "rebase-autostash":
            args.extend(("--rebase", "--autostash"))
        else:
            args.append("--%s" % (module.params["update_mode"],))
        run_git(module, dest, args)

    if dest_is_dir:
        result["after"] = run_git(module, dest, ["rev-parse", "HEAD"]).stdout
    else:
        result["after"] = None
    result["changed"] = result["changed"] or (
        result["after"] != result["before"]
    )
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
