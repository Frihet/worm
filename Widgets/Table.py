#! /bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

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
import Webwidgets.Utils

class ReadonlyTable(Webwidgets.Table, Worm.Widgets.RowsMod.RowsComposite):
    debug_queries = False
    debug_expand_info = False

    class WwModel(Worm.Widgets.RowsMod.RowsComposite.WwModel, Webwidgets.Table.WwModel):
        pass
    
    class SourceFilters(Worm.Widgets.RowsMod.RowsComposite.SourceFilters, Webwidgets.Table.SourceFilters):
        WwFilters = ['SQLAlchemyRefreshFilter'] + Webwidgets.Table.SourceFilters.WwFilters + ['SQLAlchemyFilter']

    class RowsFilters(Worm.Widgets.RowsMod.RowsComposite.RowsFilters, Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.Table.RowsFilters.WwFilters + ["StaticRowsFilter"]

class ExpandableReadonlyTable(ReadonlyTable, Webwidgets.ExpandableTable):
    """This widget allows rows to contain a "subtree row" in
    L{ww_expansion} that is inserted below the row if
    L{ww_is_expanded} is set on the row. It also adds an expand button
    that allows the user to set/reset L{ww_is_expanded}.
    """

    class RowsFilters(ReadonlyTable.RowsFilters, Webwidgets.ExpandableTable.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + ReadonlyTable.RowsFilters.WwFilters

class ExpansionReadonlyTable(ExpandableReadonlyTable, Webwidgets.ExpansionTable):
    """This widget allows any row to be "expanded" by inserting an
    extra row containing an instance of the L{ExpansionViewer} widget
    after the row if L{ww_is_expanded} is set on the row. It also adds
    an expand button that allows the user to set/reset
    L{ww_is_expanded}."""

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
    """A table that provides in-place editing of individual rows using
    SQLAlchemy sessions. The session is localized for the row (a
    transaction begun) when the user selects to edit it. It is later
    either commited or rollbacked and the globalized when the user
    selects commit or revert."""
    
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
                    self.new_version = self.object.ww_model
                    if not self.is_new():
                        #### fixme ####
                        # name = """SQLAlchemy: merge clashes with
                        # many-to-many"""
                        # description = """This uggly hack works since the
                        # object is never changed in the main session, so
                        # loading it straight from the DB will give the
                        # right attribute values."""
                        #### end ####
                        self.new_version = self.row_widget.db_session.load_from_session(self.new_version)
                    self.edit_widgets = self.new_version.get_column_input_widget_instances(
                        self.row_widget.ww_filter.db_session, self.table.session, self.table.win_id)

                def done(self):
                    self.edit_widgets = {}
                    if self.is_new():
                        self.table.ww_filter.pre_rows.remove(self.new_version)
                    del self.new_version
                    self.table.ww_filter.reread()

                def revert(self):
                    self.row_widget.db_session_rollback_and_globalize()
                    self.object.ww_filter.done()

                def save(self):
                    if self.row_widget.validate():
                        self.row_widget.db_session.save_or_update(self.new_version)
                        self.row_widget.db_session_commit_and_globalize()
                        self.object.ww_filter.done()

                def delete(self):
                    if self.is_new():
                        self.revert()
                    else:
                        if not self.row_widget.db_session_is_localized():
                            self.row_widget.db_session_localize()
                        try:
                            self.row_widget.db_session.delete(self.row_widget.db_session.load_from_session(self.object.ww_model))
                            self.row_widget.db_session_commit_and_globalize()
                        except:
                            self.row_widget.db_session_rollback_and_globalize()
                            raise
                        self.table.ww_filter.reread()

                def __getattr__(self, name):
                    if name not in ('ww_filter', 'table', 'is_new', 'ww_is_new', 'edit_widgets'):
                        cols = self.table.ww_filter.edit_columns
                        if self.is_new():
                            cols = self.table.ww_filter.edit_new_columns

                        if name in self.edit_widgets and cols.get(name, cols['ww_default']):
                            return self.edit_widgets[name]

                    return getattr(self.ww_filter, name)

    class RowsFilters(ReadonlyTable.RowsFilters, Webwidgets.EditableTable.RowsFilters):
        WwFilters = ["SQLAlchemyEditingAccesRightsFilter", "TableEditableFilter", "SQLAlchemyEditingFilter"] + ReadonlyTable.RowsFilters.WwFilters

        class SQLAlchemyEditingAccesRightsFilter(Webwidgets.Filter):
            def get_active_edit_function(self, path):
                row = self.object.ww_filter.get_row_by_id(path[-1])
                if hasattr(row, "ww_row_access"):
                    if not row.ww_row_access(path[:-1]):
                        return False
                return self.ww_filter.get_active_edit_function(path)

            def get_active_edit_group_function(self, path):
                cls = self.object.ww_filter.DBModel
                if hasattr(cls, "ww_access"):
                    if not cls.ww_access(path):
                        return False
                return self.ww_filter.get_active_edit_group_function(path)

        class SQLAlchemyEditingFilter(Webwidgets.Filter):
            def create_new_row(self):
                return self.DBModel(ww_is_new = True)


class ExpandableTable(Table, Webwidgets.ExpandableTable):
    """This widget allows rows to contain a "subtree row" in
    L{ww_expansion} that is inserted below the row if
    L{ww_is_expanded} is set on the row. It also adds an expand button
    that allows the user to set/reset L{ww_is_expanded}.
    """

    class RowsFilters(Table.RowsFilters, Webwidgets.ExpandableTable.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + Table.RowsFilters.WwFilters

class ExpansionTable(ExpandableTable, Webwidgets.ExpansionTable):
    """This widget allows any row to be "expanded" by inserting an
    extra row containing an instance of the L{ExpansionViewer} widget
    after the row if L{ww_is_expanded} is set on the row. It also adds
    an expand button that allows the user to set/reset
    L{ww_is_expanded}."""

    class RowsRowModelWrapper(ExpandableTable.RowsRowModelWrapper, Webwidgets.ExpansionTable.RowsRowModelWrapper):
        WwFilters = ["ExpansionFilter"] + ExpandableTable.RowsRowModelWrapper.WwFilters

class ExpansionEditableTable(ExpansionTable):
    """A table that provides in-place editing of individual rows with
    expansion "subtree widgets" (see L{ExpansionTable} for more details)."""

    class ExpansionEditor(Webwidgets.Widget):
        """Override this member variable with any widget to display
        beneath the rows of the table as expansion when the row is
        being edited."""

    class RowsRowModelWrapper(ExpansionTable.RowsRowModelWrapper):
        class ExpansionFilter(ExpansionTable.RowsRowModelWrapper.ExpansionFilter):
            def __init__(self, *arg, **kw):
                ExpansionTable.RowsRowModelWrapper.ExpansionFilter.__init__(self, *arg, **kw)
                if hasattr(self, 'is_expansion'): return
                self.ww_expansion['ww_expanded_old_version'] = self.ww_expansion['ww_expanded']
                if self.is_new():
                    self.edit_expansion()

            def edit_expansion(self):
                self.ww_expansion['ww_expanded'] = self.table.ExpansionEditor(
                    self.table.session, self.table.win_id,
                    db_session = self.row_widget.db_session,
                    parent_row = self.object)

            def edit(self):
                self.ww_filter.edit()
                self.edit_expansion()

            def done(self):
                self.ww_filter.done()
                self.ww_expansion['ww_expanded'] = self.ww_expansion['ww_expanded_old_version'] 



class DynamicColumnTable(ReadonlyTable):
    summary_table = None
    column_table = None

    pre_columns = Webwidgets.Utils.OrderedDict()
    column_table_columns = Webwidgets.Utils.OrderedDict()
    post_columns = Webwidgets.Utils.OrderedDict()

    pre_column_groups = Webwidgets.Utils.OrderedDict()
    post_column_groups = Webwidgets.Utils.OrderedDict()

    def get_dynamic_columns(self):
        # return [(id, title, self.column_table, column_table.id == self.summary_table.kafoo)]
        raise NotImplementedError

    @property
    @Webwidgets.Utils.Cache.cache(per_request = True, per_class=True)
    def DBModel(self):
        dynamic_columns = self.get_dynamic_columns()
        dyncol_key = hash(tuple(col[0] for col in dynamic_columns))
        if "dyncol_views" not in self.__dict__:
            self.__dict__['dyncol_views'] = {}
        if dyncol_key not in self.dyncol_views:
            cols = [self.summary_table]
            joins = []
            for column_id, column_title, column_table, column_where in dynamic_columns:
                for column_table_column_name, column_table_column_title in self.column_table_columns.iteritems():
                    cols.append(
                        sqlalchemy.func.coalesce(getattr(column_table.c, column_table_column_name),
                                                 0.0).label("dyncol_%s_%s" % (column_id, column_table_column_name)))
                joins.append((column_table, column_where))
            class DynamicColumnView(ReadonlyTable.WwModel.DBModel):
                table = sqlalchemy.select(
                    cols,
                    self.db_dynamic_where(dynamic_columns),
                    from_obj=[Argentum.outerjoin(self.summary_table, *joins)]).distinct().alias("dynamiccolumnview")
            sqlalchemy.orm.mapper(DynamicColumnView, DynamicColumnView.table)
            self.dyncol_views[dyncol_key] = DynamicColumnView
        return self.dyncol_views[dyncol_key]

    def db_dynamic_where(self, dynamic_columns):
        return Argentum.True_

    @property
    @Webwidgets.Utils.Cache.cache(per_request = True, per_class=True)
    def columns(self):
        res = Webwidgets.Utils.OrderedDict()
        for column_id, column_title, column_table, column_where in self.get_dynamic_columns():
            for (name, title) in self.column_table_columns.iteritems():
                res["dyncol_%s_%s" % (column_id, name)] = {'title': name, 'dyncol':column_id}
        return self.pre_columns + res + self.post_columns

    @property
    @Webwidgets.Utils.Cache.cache(per_request = True, per_class=True)
    def column_groups(self):
        return (  self.pre_column_groups
                + Webwidgets.Utils.OrderedDict([('dyncol',
                                                 Webwidgets.Utils.OrderedDict(dynamic_column[:2]
                                                                              for dynamic_column
                                                                              in self.get_dynamic_columns()))])
                + self.post_column_groups)
