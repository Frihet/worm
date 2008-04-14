#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Lumbricidae Worm widget object relational mapper
# Copyright (C) 2008 FreeCode AS, Egil Moeller <egil.moeller@freecode.no>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import Webwidgets
import Worm.Utils, Worm.Model.Base, Worm.Widgets.Base, Worm.Widgets.RowsMod, math, sqlalchemy.sql, itertools, types

class RowsListInput(Webwidgets.RowsListInput, Worm.Widgets.RowsMod.RowsComposite, Worm.Widgets.Base.Widget):
    debug_queries = False
    debug_expand_info = False

    class WwModel(Webwidgets.RowsListInput.WwModel, Worm.Widgets.RowsMod.RowsComposite.WwModel):
        pass
    
    class SourceFilters(Worm.Widgets.RowsMod.RowsComposite.SourceFilters, Webwidgets.Table.SourceFilters):
        WwFilters = Webwidgets.RowsListInput.SourceFilters.WwFilters + ['SQLAlchemyFilter']

    class RowsFilters(Worm.Widgets.RowsMod.RowsComposite.RowsFilters, Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.RowsListInput.RowsFilters.WwFilters + ["StaticRowsFilter"]

class RowsSingleValueListInput(RowsListInput, Webwidgets.RowsSingleValueListInput):
    pass
