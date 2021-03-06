#!/usr/bin/env python3

############################################################################
#
# MODULE:       g.extension.github
# AUTHOR(S):    Anika Weinmann
# PURPOSE:      Tool to download and install extensions (Addons) from official
#               GRASS GIS Addons GitHub (https://github.com/OSGeo/grass-addons)
#               using g.extension
#
# COPYRIGHT:    (C) 2021-2022 by mundialis GmbH & Co. KG and the GRASS Development Team
#
#               This program is free software; you can redistribute it and/or modify
#               it under the terms of the GNU General Public License (>=v2) as published
#               by the Free Software Foundation; either version 2 of the License, or
#               (at your option) any later version.
#
#               This program is distributed in the hope that it will be useful,
#               but WITHOUT ANY WARRANTY; without even the implied warranty of
#               MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#               GNU General Public License for more details.
#
#############################################################################

# %module
# % description: Downloads and installs extensions from GRASS Addons repository using g.extension
# % keyword: general
# % keyword: installation
# % keyword: extensions
# % keyword: addons
# % keyword: download
# % keyword: github
# %end

# %option
# % key: extension
# % type: string
# % key_desc: name
# % label: Name of extension to install or remove
# % description: Name of toolbox (set of extensions) when -t flag is given
# % required: yes
# %end

# %option
# % key: operation
# % type: string
# % description: Operation to be performed
# % required: yes
# % options: add,remove
# % answer: add
# %end

# %option
# % key: reference
# % type: string
# % key_desc: Branch or commit hash as reference
# % description: Specific branch or commit hash to fetch addon
# % required: no
# % multiple: no
# % answer: main
# %end

# %flag
# % key: s
# % description: Install system-wide (may need system administrator rights)
# % guisection: Install
# %end

# %flag
# % key: f
# % description: Force removal when uninstalling extension (operation=remove)
# % guisection: Remove
# %end

import atexit
import json
import os
import shutil
import sys
import base64
import urllib.request

import grass.script as grass

try:
    import requests
except ImportError:
    grass.fatal(
        _(
            "Cannot import requests (https://docs.python-requests.org/en/latest/)"
            " library."
            " Please install it (pip install requests)"
            " or ensure that it is on path"
            " (u se PYTHONPATH variable)."
        )
    )


rm_folders = []
curr_path = None
GIT_URL = "https://github.com/OSGeo/grass-addons"
RAW_URL = "https://raw.githubusercontent.com/OSGeo/grass-addons"
API_URL = "https://api.github.com/repos/OSGeo/grass-addons/contents"


def cleanup():
    grass.message(_("Cleaning up..."))
    for folder in rm_folders:
        if os.path.isdir(folder):
            shutil.rmtree(folder)
    if curr_path is not None:
        os.chdir(curr_path)


def get_module_class(module_name):
    class_letters = module_name.split(".", 1)[0]
    name = {
        "d": "display",
        "db": "db",
        "g": "general",
        "i": "imagery",
        "m": "misc",
        "ps": "postscript",
        "p": "paint",
        "r": "raster",
        "r3": "raster3d",
        "s": "sites",
        "t": "temporal",
        "v": "vector",
        "wx": "gui/wxpython",
    }
    return name.get(class_letters, class_letters)


def urlopen_with_auth(url):
    request = urllib.request.Request(url)
    if "GITHUB_TOKEN" in os.environ and "GITHUB_USERNAME" in os.environ:
        base64string = base64.b64encode((f"{os.environ['GITHUB_USERNAME']}:{os.environ['GITHUB_TOKEN']}").encode())
        request.add_header("Authorization", "Basic %s" % base64string)
    return urllib.request.urlopen(request)


def urlretrieve_with_auth(url, path):
    session = requests.Session()
    if "GITHUB_TOKEN" in os.environ and "GITHUB_USERNAME" in os.environ:
        session.auth = (
            os.environ['GITHUB_USERNAME'],
            os.environ['GITHUB_TOKEN']
        )
    response = session.get(url, stream=True)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            f.write(response.content)


def download_git(gitapi_url, git_url, reference, tmp_dir, lstrip=2):
    """
    Downloading a folder of github with urllib.request based on Stefan
    Blumentrath code from https://github.com/OSGeo/grass/issues/625.
    """
    req = urlopen_with_auth(f"{gitapi_url}?ref={reference}")
    content = json.loads(req.read())
    # directories = []
    for element in content:
        path = os.path.join(tmp_dir, *element["path"].split("/")[lstrip:])
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        if element["download_url"] is not None:
            file = os.path.basename(element["download_url"])
            url = f"{git_url}/{file}"
            urlretrieve_with_auth(url, path)
        else:
            download_git(
                f"{gitapi_url}/{element['name']}",
                f"{git_url}/{element['name']}",
                reference,
                tmp_dir
            )


def main():

    global rm_folders

    extension = options["extension"]
    operation = options["operation"]
    reference = options["reference"]

    gextension_flags = ""
    if flags["f"]:
        gextension_flags += "f"
    if flags["s"]:
        gextension_flags += "s"

    if operation == "remove":
        grass.run_command(
            "g.extension",
            extension=extension,
            operation=operation,
            flags=gextension_flags,
        )
    elif operation == "add" and reference == "main":
        grass.run_command(
            "g.extension",
            extension=extension,
            operation=operation,
            flags=gextension_flags,
        )
    elif operation == "add" and reference != "main":
        """
        Download folder from github using Python3 moudule 'git' and
        the configuration in git 'core.sparseCheckout'
        (https://stackoverflow.com/questions/33066582/how-to-download-a-folder-from-github/48948711).
        This installation takes for i.sentinel about 45 sec
        (very long compared to 8 sec (reference value is from g.extension)).
        """
        """
        try:
            from git import Repo
        except Exception as e:
            grass.fatal(_("Python module 'git' is not installed. Please "
                "install it with e.g. <python -m pip install gitpython>"))
        # mkdir folder && cd folder
        new_repo_path = grass.tempdir()
        rm_folders.append(new_repo_path)
        # git init
        new_repo = Repo.init(new_repo_path)
        # git remote add origin https://github.com/OSGeo/grass-addons.git
        origin = new_repo.create_remote(
            'origin', 'https://github.com/OSGeo/grass-addons.git')
        curr_path = os.getcwd()
        os.chdir(new_repo_path)
        # git config core.sparseCheckout true
        process = subprocess.run(
            ['git', 'config', 'core.sparseCheckout', 'true'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if process.stderr != b'':
            grass.fatal(_("Configuring the single extension does not work: "
                "<git config core.sparseCheckout true> failed"))
        # echo "grass8/imagery/i.sentinel"  > .git/info/sparse-checkout
        gversion = "grass{}".format(grass.version()['version'].split('.')[0])
        ext_type = get_module_class(extension)
        extension_folder = "{}/{}/{}".format(gversion, ext_type, extension)
        with open('.git/info/sparse-checkout', 'w') as git_conf:
            git_conf.write(extension_folder)
        # git pull origin master
        origin.pull('master')
        # git checkout -b hash_branch 0e61c94d2b4aab5f22a6b001cf0b2dc2c46662ba
        try:
            new_repo.git.checkout(reference, b="hash_branch")
        except Exception as e:
            grass.fatal(_("Reference <{}> not found".format(reference)))
        os.chdir(curr_path)
        extension_path = os.path.join(new_repo_path, extension_folder)
        """

        """
        Downloading a folder of github with urllib.request based on Stefan
        Blumentrath code from https://github.com/OSGeo/grass/issues/625.
        """
        # code based
        ext_type = get_module_class(extension)

        extension_folder = "src/{}/{}".format(ext_type, extension)
        gitapi_url = f"{API_URL}/{extension_folder}"
        git_url = f"{RAW_URL}/{reference}/src/{ext_type}/{extension}"
        new_repo_path = grass.tempdir()
        rm_folders.append(new_repo_path)
        try:
            download_git(gitapi_url, git_url, reference, new_repo_path)
        except Exception as e:
            grass.fatal(
                _(
                    "Could not find extension in repository.\n"
                    f"Searching in repo path {extension_folder}\n"
                    f"for reference {reference}.\n"
                    f"{e}"
                )
            )
        extension_path = os.path.join(new_repo_path, extension)

        """
        Install addon with g.extension
        """
        grass.run_command(
            "g.extension",
            extension=extension,
            url=extension_path,
            operation=operation,
            flags=gextension_flags,
        )

    else:
        grass.warning(_("Nothing done"))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
