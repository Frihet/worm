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

class ReadonlyTable(Webwidgets.Table, Worm.Widgets.RowsMod.RowsComposite, Worm.Widgets.Base.Widget):
    debug_queries = False
    debug_expand_info = False

    class WwModel(Worm.Widgets.RowsMod.RowsComposite.WwModel, Webwidgets.Table.WwModel):
        pass
    
    class SourceFilters(Worm.Widgets.RowsMod.RowsComposite.SourceFilters, Webwidgets.Table.SourceFilters):
        WwFilters = Webwidgets.Table.SourceFilters.WwFilters + ['SQLAlchemyFilter']

    class RowsFilters(Worm.Widgets.RowsMod.RowsComposite.RowsFilters, Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.Table.RowsFilters.WwFilters + ["StaticRowsFilter"]


class Table(ReadonlyTable, Webwidgets.EditableTable):
    class RowsRowModelWrapper(Webwidgets.EditableTable.RowsRowModelWrapper, ReadonlyTable.RowsRowModelWrapper):
        WwFilters = ["EditingFilters"] + ReadonlyTable.RowsRowModelWrapper.WwFilters
        
        class EditingFilters(Webwidgets.EditableTable.RowsRowModelWrapper.EditingFilters):
            WwFilters = ["SQLAlchemyEditingFilter"] + Webwidgets.EditableTable.RowsRowModelWrapper.EditingFilters.WwFilters
            
            class SQLAlchemyEditingFilter(Webwidgets.Filter):
                def __init__(self, *arg, **kw):
                    Webwidgets.Filter.__init__(self, *arg, **kw)
                    object.__setattr__(self, 'edit_widgets', {})
                    if self.is_new():
                        self.edit()

                def is_new(self):
                    return getattr(self, 'ww_is_new', False)

                def is_editing(self):
                    return self.edit_widgets != {}

                def edit(self):
                    if self.edit_widgets: return
                    self.edit_session = self.table.db_session.bind.Session()
                    if self.is_new():
                        self.new_version = self.edit_session.save_and_expire(self.object.ww_model)
                    else:
                        #### fixme ####
                        # name = """SQLAlchemy: merge clashes with
                        # many-to-many"""
                        # description = """Uggly hack since merge does not
                        # seem to work when you have many-to-many
                        # relationships!!! This uggly hack works since the
                        # object is never changed in the main session, so
                        # loading it straight from the DB will give the
                        # right attribute values."""
                        #### end ####
                        #self.new_version = self.edit_session.merge(self.object.ww_model)
                        t = type(self.object.ww_model)
                        self.new_version = self.edit_session.query(t).filter(t.id == self.object.ww_model.id)[0]
                    self.edit_widgets = self.new_version.get_column_input_widget_instances(
                        self.edit_session, self.table.session, self.table.win_id)

                def revert(self):
                    self.edit_session.close()
                    self.edit_widgets = {}
                    if self.is_new():
                        self.table.pre_rows.remove(self.object.ww_model)

                def save(self):
                    self.edit_session.commit()
                    self.object.ww_model.expire()
                    self.table.ww_filter.reread()
                    self.object.ww_filter.revert()
                    self.new_version.ww_is_new = False

                def delete(self):
                    if self.is_new():
                        self.revert()
                    else:
                        self.table.db_session.delete(self.object)
                        self.table.db_session.commit()
                        self.table.ww_filter.reread()

                def __getattr__(self, name):
                    if name in self.edit_widgets:
                        return self.edit_widgets[name]
                    return getattr(self.ww_filter, name)

    class RowsFilters(ReadonlyTable.RowsFilters, Webwidgets.EditableTable.RowsFilters):
        WwFilters = ["TableEditableFilter"] + ReadonlyTable.RowsFilters.WwFilters

class ExpandableTable(Table, Webwidgets.ExpandableTable):
    class RowsFilters(Table.RowsFilters, Webwidgets.ExpandableTable.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + Table.RowsFilters.WwFilters

class ExpansionEditableTable(ExpandableTable):
    class RowsRowModelWrapper(ExpandableTable.RowsRowModelWrapper):
        class EditingFilters(ExpandableTable.RowsRowModelWrapper.EditingFilters):
            WwFilters = ["ExpansionEditingFilter"] + ExpandableTable.RowsRowModelWrapper.EditingFilters.WwFilters

            class ExpansionEditingFilter(Webwidgets.Filter):
                def __init__(self, *arg, **kw):
                    Webwidgets.Filter.__init__(self, *arg, **kw)
                    if hasattr(self, 'is_expansion'): return
                    self.ww_expansion = {
                        'is_expansion': True,
                        'ww_functions': [],
                        'ww_expanded': self.table.ExpansionViewer(
                        self.table.session, self.table.win_id,
                        parent_table = self)}
                    self.ww_expansion['ww_expanded_old_version'] = self.ww_expansion['ww_expanded']
                    if self.is_new():
                        self.edit_expansion()

                def edit_expansion(self):
                    self.ww_expansion['ww_expanded'] = self.table.ExpansionEditor(
                        self.table.session, self.table.win_id,
                        edit_session = self.edit_session,
                        parent_table = self.new_version)

                def edit(self):
                    self.ww_filter.edit()
                    self.edit_expansion()

                def revert(self):
                    self.ww_filter.revert()
                    self.ww_expansion['ww_expanded'] = self.ww_expansion['ww_expanded_old_version'] 
