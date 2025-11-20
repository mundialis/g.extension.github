#!/usr/bin/env python3

############################################################################
#
# MODULE:       g.extension.github
# AUTHOR(S):    Markus Neteler
# PURPOSE:      Tests g.extension.github GRASS module
#
# COPYRIGHT:    (C) 2022 mundialis GmbH & Co. KG and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class Testg_extension_github(TestCase):
    """Test g.extension.github script with a multi-module and specific commit hash."""

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove extension."""
        cls.runModule(
            "g.extension.github",
            extension="i.sentinel",
            operation="remove",
            flags="f",
        )

    def test_g_extension_github(self) -> None:
        """Install i.sentinel extension with specific commit hash. The test is slow."""
        ghHash = "aff69a9a0dac8c68ccb877858675d84588b35bd2"
        module = SimpleModule(
            "g.extension.github",
            extension="i.sentinel",
            reference=ghHash,
            flags="f",
        )
        self.assertModule(module)


if __name__ == "__main__":
    test()
