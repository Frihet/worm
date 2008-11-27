#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

"""
Lumbricidae Worm widget object relational mapper

 - Copyright (C) 2008 FreeCode AS, Egil Moeller <egil.moller@freecode.no>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
USA


About
=====

    Worm is a library of Webwidgets widgets that interact with
    SQLAlchemy database mapped classes and instances.

    Worm also provides mix-in classes for SQLAlchemy mapped classes
    that provides integration with Webwidgets and automation of common
    tasks, such as selecting a proper input widget for a database
    column (according to its declared type).
"""

# This check is here because Webware might erraneously import us with
# the wrong name first, when loading an index.py-file from the Demo
# directory. Doing so makes us have copies of some classes, which
# fucks up isinstance()-calls.
if __name__ == "Worm":
    from Session import *
    from Program import *
    from Widgets.Base import *
    from Widgets.RowsMod import *
    from Widgets.ListMod import *
    from Widgets.Table import *
