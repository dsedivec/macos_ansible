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
module: git_remote

short_description: Add, change, or delete remotes in a Git repository

version_added: "2.8"

description:
    - "TBD"

options: TBD

extends_documentation_fragment: TBD

author:
    - Dale Sedivec (@dsedivec)
"""

EXAMPLES = "TBD"

RETURN = "TBD"

# fmt: off

from ansible.module_utils.basic import AnsibleModule
import pathlib

# fmt: on


def test_for_git_repo(repo_dir, module, git):
    # Test if this is even a git repo.
    return module.run_command([git, "rev-parse", "--git-dir"], cwd=repo_dir)


def run_module():
    module_args = dict(
        dest=dict(type="path", required=True),
        repo=dict(type="str", required=False, default=None),
        remote=dict(type="str", required=True),
        state=dict(type="str", choices=("present", "absent"), required=True),
        git=dict(type="path", required=False, default="git"),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    params = module.params
    state = params["state"]
    dest = pathlib.Path(params["dest"])
    new_url = params["repo"]
    remote_name = params["remote"]
    git = params["git"]
    result = dict(changed=False)

    # Note: I should have just used run_command(check_rc=True), which
    # I only found out about after writing this whole module.
    def run_command(args, *, fail_msg, ok_rcs=(0,), **kwargs):
        rc, out, err = module.run_command(args, **kwargs)
        if rc in ok_rcs:
            return rc, out
        module.fail_json(msg=fail_msg, stdout=out, stderr=err, rc=rc, **result)

    def ensure_git_repo(path):
        run_command(
            [git, "rev-parse", "--git-dir"],
            cwd=path,
            fail_msg=f"{dest} is not a Git repository",
        )

    def get_remote_url(repo_dir, remote_name):
        rc, out = run_command(
            [git, "config", f"remote.{remote_name}.url"],
            cwd=repo_dir,
            ok_rcs=(0, 1),
            fail_msg="git config exited with unexpected status value",
        )
        return rc == 0, out.strip() if rc == 0 else None

    if state == "present":
        if new_url is None:
            module.fail_json(
                msg='"repo" parameter is required with state=present', **result
            )
        if dest.is_dir():
            ensure_git_repo(dest)
            result["cloned"] = False
            remote_exists, old_url = get_remote_url(dest, remote_name)
            if remote_exists:
                if old_url != new_url:
                    if module.check_mode:
                        msg = (
                            "Would have changed URL of remote %s from %s to %s"
                            % (remote_name, old_url, new_url)
                        )
                    else:
                        run_command(
                            [git, "remote", "set-url", remote_name, new_url],
                            cwd=dest,
                            fail_msg="git remote set-url exited non-zero",
                        )
                        msg = "Changed URL of remote %s from %s to %s" % (
                            remote_name,
                            old_url,
                            new_url,
                        )
                    result.update(
                        old_repo=old_url,
                        new_repo=new_url,
                        changed=True,
                        msg=msg,
                    )
            else:
                if module.check_mode:
                    msg = "Would have created remote %s with URL %s" % (
                        remote_name,
                        new_url,
                    )
                else:
                    run_command(
                        [git, "remote", "add", remote_name, new_url],
                        cwd=dest,
                        fail_msg="git remote add failed",
                    )
                    msg = "Created remote %s with URL %s" % (
                        remote_name,
                        new_url,
                    )
                result.update(new_repo=new_url, changed=True, msg=msg)
        else:
            if module.check_mode:
                msg = "Would have cloned new repo"
            else:
                run_command(
                    [git, "clone", "-o", remote_name, new_url],
                    cwd=dest.parent,
                    fail_msg="git clone failed",
                )
                msg = "Cloned new repo %s with remote %s = %s" % (
                    dest,
                    remote_name,
                    new_url,
                )
            result.update(cloned=True, new_repo=new_url, changed=True, msg=msg)
    elif state == "absent":
        if dest.is_dir():
            ensure_git_repo(dest)
            remote_exists, old_url = get_remote_url(dest, remote_name)
            if remote_exists:
                if new_url is None or old_url == new_url:
                    if module.check_mode:
                        msg = f"Would have deleted remote {remote_name}"
                    else:
                        run_command(
                            [git, "remote", "remove", remote_name],
                            cwd=dest,
                            fail_msg="git remote remove failed",
                        )
                        msg = f"Deleted remote {remote_name}"
                    result.update(old_url=old_url, changed=True, msg=msg)
                elif new_url is not None:
                    assert old_url != new_url
                    module.fail_json(
                        msg=(
                            "Remote %s has URL %r, not the expected %r"
                            % (remote_name, old_url, new_url)
                        ),
                        **result,
                    )
            else:
                result["msg"] = f"Remote {remote_name} does not exist"
        else:
            module.fail_json(msg=f"Repo {dest} does not exist", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
