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
import Argentum, Worm.Model.Base, Worm.Widgets.Base, Worm.Widgets.RowsMod, math, sqlalchemy.sql, itertools, types

class ReadonlyTable(Webwidgets.Table, Worm.Widgets.RowsMod.RowsComposite, Worm.Widgets.Base.Widget):
    debug_queries = False
    debug_expand_info = False

    class WwModel(Worm.Widgets.RowsMod.RowsComposite.WwModel, Webwidgets.Table.WwModel):
        pass
    
    class SourceFilters(Worm.Widgets.RowsMod.RowsComposite.SourceFilters, Webwidgets.Table.SourceFilters):
        WwFilters = Webwidgets.Table.SourceFilters.WwFilters + ['SQLAlchemyFilter']

    class RowsFilters(Worm.Widgets.RowsMod.RowsComposite.RowsFilters, Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.Table.RowsFilters.WwFilters + ["StaticRowsFilter"]

class ExpandableReadonlyTable(ReadonlyTable, Webwidgets.ExpandableTable):
    class RowsFilters(ReadonlyTable.RowsFilters, Webwidgets.ExpandableTable.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + ReadonlyTable.RowsFilters.WwFilters

class ExpansionReadonlyTable(ExpandableReadonlyTable):
    class RowsRowModelWrapper(ExpandableReadonlyTable.RowsRowModelWrapper):
        WwFilters = ["ExpansionFilter"] + ExpandableReadonlyTable.RowsRowModelWrapper.WwFilters

        class ExpansionFilter(Webwidgets.Filter):
            def __init__(self, *arg, **kw):
                Webwidgets.Filter.__init__(self, *arg, **kw)
                if hasattr(self, 'is_expansion'): return
                self.ww_expansion = {
                    'is_expansion': True,
                    'ww_functions': [],
                    'ww_expanded': self.table.ExpansionViewer(
                    self.table.session, self.table.win_id,
                    parent_row = self.object)}


class Table(ReadonlyTable, Webwidgets.EditableTable):
    class WwModel(ReadonlyTable.WwModel, Webwidgets.EditableTable.WwModel):
        pass

    class RowsRowWidget(Webwidgets.EditableTable.RowsRowWidget, Worm.Widgets.Base.Widget): pass

    class RowsRowModelWrapper(Webwidgets.EditableTable.RowsRowModelWrapper, ReadonlyTable.RowsRowModelWrapper):
        WwFilters = ["EditingFilters"] + ReadonlyTable.RowsRowModelWrapper.WwFilters
        
        class EditingFilters(Webwidgets.EditableTable.RowsRowModelWrapper.EditingFilters):
            WwFilters = ["SQLAlchemyEditingFilter"] + Webwidgets.EditableTable.RowsRowModelWrapper.EditingFilters.WwFilters
            
            class SQLAlchemyEditingFilter(Webwidgets.Filter):
                def __init__(self, *arg, **kw):
                    Webwidgets.Filter.__init__(self, *arg, **kw)
                    object.__setattr__(self, 'edit_widgets', {})
                    self.row_widget = self.table.child_for_row(self.object)
                    if self.is_new():
                        self.edit()

                def is_new(self):
                    return getattr(self, 'ww_is_new', False)

                def is_editing(self):
                    return self.edit_widgets != {}

                def edit(self):
                    if self.edit_widgets: return
                    self.row_widget.db_session_localize()
                    if self.is_new():
                        self.new_version = self.row_widget.db_session.save_and_expire(self.object.ww_model)
                    else:
                        #### fixme ####
                        # name = """SQLAlchemy: merge clashes with
                        # many-to-many"""
                        # description = """This uggly hack works since the
                        # object is never changed in the main session, so
                        # loading it straight from the DB will give the
                        # right attribute values."""
                        #### end ####
                        self.new_version = self.row_widget.db_session.load_from_session(self.object.ww_model)
                    self.edit_widgets = self.new_version.get_column_input_widget_instances(
                        self.row_widget.db_session, self.table.session, self.table.win_id)

                def done(self):
                    self.edit_widgets = {}
                    if self.is_new():
                        self.table.pre_rows.remove(self.object.ww_model)
                    self.table.ww_filter.reread()

                def revert(self):
                    self.row_widget.db_session_rollback_and_globalize()
                    self.object.ww_filter.done()

                def save(self):
                    self.row_widget.db_session_commit_and_globalize()
                    self.row_widget.db_session.expire()
                    self.object.ww_filter.done()
                    self.new_version.ww_is_new = False

                def delete(self):
                    if self.is_new():
                        self.revert()
                    else:
                        self.row_widget.table.db_session.delete(self.object)
                        self.row_widget.table.db_session.commit()
                        self.table.ww_filter.reread()

                def __getattr__(self, name):
                    if name not in ('table', 'ww_is_new'):
                        cols = self.table.ww_filter.edit_columns
                        if self.is_new():
                            cols = self.table.ww_filter.edit_new_columns

                        if name in self.edit_widgets and cols.get(name, cols['ww_default']):
                            return self.edit_widgets[name]

                    return getattr(self.ww_filter, name)

    class RowsFilters(ReadonlyTable.RowsFilters, Webwidgets.EditableTable.RowsFilters):
        WwFilters = ["TableEditableFilter", "SQLAlchemyEditingFilter"] + ReadonlyTable.RowsFilters.WwFilters

        class SQLAlchemyEditingFilter(Webwidgets.Filter):
            def create_new_row(self):
                return self.DBModel(ww_is_new = True)


class ExpandableTable(Table, Webwidgets.ExpandableTable):
    class RowsFilters(Table.RowsFilters, Webwidgets.ExpandableTable.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + Table.RowsFilters.WwFilters

class ExpansionTable(ExpandableTable):
    class RowsRowModelWrapper(ExpandableTable.RowsRowModelWrapper):
        class EditingFilters(ExpandableTable.RowsRowModelWrapper.EditingFilters):
            WwFilters = ["ExpansionFilter"] + ExpandableTable.RowsRowModelWrapper.EditingFilters.WwFilters

            class ExpansionFilter(Webwidgets.Filter):
                def __init__(self, *arg, **kw):
                    Webwidgets.Filter.__init__(self, *arg, **kw)
                    if hasattr(self, 'is_expansion'): return
                    self.ww_expansion = {
                        'is_expansion': True,
                        'ww_functions': [],
                        'ww_expanded': self.table.ExpansionViewer(
                        self.table.session, self.table.win_id,
                        parent_row = self.object)}

class ExpansionEditableTable(ExpansionTable):
    class RowsRowModelWrapper(ExpansionTable.RowsRowModelWrapper):
        class EditingFilters(ExpansionTable.RowsRowModelWrapper.EditingFilters):
            class ExpansionFilter(ExpansionTable.RowsRowModelWrapper.EditingFilters.ExpansionFilter):
                def __init__(self, *arg, **kw):
                    ExpansionTable.RowsRowModelWrapper.EditingFilters.ExpansionFilter.__init__(self, *arg, **kw)
                    if hasattr(self, 'is_expansion'): return
                    self.ww_expansion['ww_expanded_old_version'] = self.ww_expansion['ww_expanded']
                    if self.is_new():
                        self.edit_expansion()

                def edit_expansion(self):
                    self.ww_expansion['ww_expanded'] = self.table.ExpansionEditor(
                        self.table.session, self.table.win_id,
                        db_session = self.db_session,
                        parent_row = self.object)

                def edit(self):
                    self.ww_filter.edit()
                    self.edit_expansion()

                def revert(self):
                    self.ww_filter.revert()
                    self.ww_expansion['ww_expanded'] = self.ww_expansion['ww_expanded_old_version'] 
