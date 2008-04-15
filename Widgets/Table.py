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


class EditFunctionCell(Webwidgets.FunctionCell):
    html_class = ['edit_function_col']

    input_path = ['edit']

    edit_function_titles = {'edit': 'Edit',
                            'save': 'Save',
                            'revert': 'Revert',
                            'delete': 'Delete'}

    def draw_edit_function(self, table, row_id, is_editing, active, output_options):
        if is_editing:
            functions = ('save', 'revert', 'delete')
        else:
            functions = ('edit', 'delete')
            
        res = ''
        for function in functions:
            res += self.draw_function(table,
                                      row_id, row_id,
                                      ['edit_function', function],
                                      function,
                                      self.edit_function_titles[function],
                                      active, output_options)
        return res
    
    def draw_table_cell(self, output_options, row, table, row_num, column_name, rowspan, colspan, first_level, last_level):
        row_id = table.ww_filter.get_row_id(row)
        return self.draw_edit_function(table, row_id,
                                       row.ww_filter.is_editing(),
                                       table.get_active(table.path + ['_', 'edit_function']),
                                       output_options)

EditFunctionCellInstance = EditFunctionCell()


class ReadonlyTable(Webwidgets.Table, Worm.Widgets.RowsMod.RowsComposite, Worm.Widgets.Base.Widget):
    debug_queries = False
    debug_expand_info = False

    class WwModel(Webwidgets.Table.WwModel, Worm.Widgets.RowsMod.RowsComposite.WwModel):
        pass
    
    class SourceFilters(Worm.Widgets.RowsMod.RowsComposite.SourceFilters, Webwidgets.Table.SourceFilters):
        WwFilters = Webwidgets.Table.SourceFilters.WwFilters + ['SQLAlchemyFilter']

    class RowsFilters(Worm.Widgets.RowsMod.RowsComposite.RowsFilters, Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.Table.RowsFilters.WwFilters + ["StaticRowsFilter"]


class Table(ReadonlyTable):
    # ('edit_group_function', {'level': 1})

    
    class RowsRowModelWrapper(ReadonlyTable.RowsRowModelWrapper):
        WwFilters = ["EditingFilter"] + ReadonlyTable.RowsRowModelWrapper.WwFilters

        class EditingFilter(Webwidgets.Filter):
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
                    self.new_version = old_version = self.edit_session.save_and_expire(self.object.ww_model)
                else:
                    self.new_version = old_version = self.edit_session.merge(self.object.ww_model)
                    self.new_version = self.new_version.copy()
                    self.edit_session.save(self.new_version)
                    old_version.is_current = False
                self.edit_widgets = self.new_version.get_column_input_widget_instances(
                    self.edit_session, self.table.session, self.table.win_id)
                
            def revert(self):
                self.edit_session.close()
                self.edit_widgets = {}
                if self.is_new():
                    self.table.pre_rows.remove(self.object.ww_model)
                    
            def save(self):
                self.edit_session.commit()
                self.table.ww_filter.reread()
                self.revert()
                self.new_version.ww_is_new = False

            def delete(self):
                if self.is_new():
                    self.revert()
                else:
                    self.object.is_current = False
                    self.table.db_session.commit()
                    self.table.ww_filter.reread()

            def __getattr__(self, name):
                if name in self.edit_widgets:
                    return self.edit_widgets[name]
                return getattr(self.ww_filter, name)

    def field_input_edit_group_function(self, path, string_value):
        if string_value == '': return
        if path[0] == "new":
            self.pre_rows.append(self.DBModel(ww_is_new = True))

    def field_output_edit_group_function(self, path):
        return []
    
    def draw_edit_group_function(self, config, output_options):
        return True, self.draw_group_function(['edit_group_function', "new"],
                                              "new",
                                              "Add new",
                                              output_options)

    def get_active_edit_group_function(self, path):
        return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, self.path + ['edit_group_function'] + path)

    class RowsFilters(ReadonlyTable.RowsFilters):
        class TableEditableFilter(Webwidgets.Filter):
            def get_rows(self, all, output_options):
                res = []
                for row in self.ww_filter.get_rows(all, output_options):
                    row.edit_function_col = EditFunctionCellInstance
                    res.append(row)
                return res

            def field_input_edit_function(self, path, string_value):
                if string_value == '': return
                row = self.object.ww_filter.get_row_by_id(string_value)
                function = path[0]	
                if function == "edit":
                    row.ww_filter.edit()
                elif function == "revert":
                    row.ww_filter.revert()
                elif function == "save":
                    row.ww_filter.save()
                elif function == "delete":
                    row.ww_filter.delete()
                    
            def field_output_edit_function(self, path):
                return []

            def get_active_edit_function(self, path):
                return self.session.AccessManager(Webwidgets.Constants.EDIT, self.win_id, self.path + ['edit'] + path)

        WwFilters = ["TableEditableFilter"] + ReadonlyTable.RowsFilters.WwFilters


class ExpandableTable(Table, Webwidgets.ExpandableTable):
    class RowsFilters(Table.RowsFilters, Webwidgets.ExpandableTable.RowsFilters):
        WwFilters = ["TableExpandableFilter"] + Table.RowsFilters.WwFilters

class ExpansionEditableTable(ExpandableTable):
    class RowsRowModelWrapper(Table.RowsRowModelWrapper):
        WwFilters = ["ExpansionEditingFilter"] + ExpandableTable.RowsRowModelWrapper.WwFilters
                
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
                self.ww_expansion['ww_expanded_old_version'] = self.ww_expansion['ww_expanded']
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
