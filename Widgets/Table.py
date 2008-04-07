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
import Worm.Utils, Worm.Model.Base, math, sqlalchemy.sql, itertools, types

class ReadonlyTable(Webwidgets.Table):
    debug_queries = False
    debug_expand_info = False

    class WwModel(Webwidgets.Table.WwModel):
        db_where = None
        """This is a filter to be applied to all database queries,
        prior to any sorting, expansion etc. It can be any SQLAlchemy
        SQL Expression expression."""
        
        class DBModel(Worm.Model.Base.BaseModel):
            """This is the database model used by the table. This
            class must be subclassed and mapped using SQLAlchemy. It
            requires the mapped table to be available in the table
            attribute (this is fullfilled automatically if you are
            using elixir)."""
            
            def __getattr__(self, name):
                if name == "ww_row_id":
                    return self.id
                raise AttributeError(self, name)

            def get_column_from_alias(cls, alias, col):
                return getattr(alias.c, ("%s_%s_%s" % (cls.__module__.replace('.', '_'), cls.__name__, col)).lower())
            get_column_from_alias = classmethod(get_column_from_alias)

        pre_rows = []
        post_rows = []
    
    class SourceFilters(Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.Table.SourceFilters.WwFilters + ['SQLAlchemyFilter']

        class SQLAlchemyFilter(Webwidgets.Filter):
            non_memory_storage = True

            def get_row_query(self, all, output_options):
                expand_tree = self.get_expand_tree()
                query = self.session.db.query(self.DBModel)
                if self.db_where is not None:
                    query = query.filter(self.db_where)

                # We need a complete ordering, so that the sorting is
                # deterministic and stable over reloads...
                sort = self.sort + [('id', 'asc')]

                # Define a way to filter the rows to remove children of
                # collapsed rows.
                if self.default_expand:
                    # This should be recognizable from the pure in-memory
                    # algoritm used in Webwidgets.Table.
                    def tree_to_filter(node):
                        if node.toggled:
                            return self.DBModel.id.in_(node.rows.keys())
                        else:
                            whens = []
                            for value, sub in node.values.iteritems():
                                whens.append((getattr(self.DBModel, node.col) == value,
                                             tree_to_filter(sub)))
                            if whens:
                                return sqlalchemy.sql.case(whens, else_ = Worm.Utils.True_)
                            else:
                                return Worm.Utils.True_
                else:
                    # OK, this is a bit uggly, but there is no other way in SQL :(
                    # This computes the previous line (per the sorting order) of each line
                    prev_row_id = query.compile().alias()
                    row_cmp = Worm.Utils.False_
                    for col, order in reversed(sort):
                        prev_col = self.DBModel.get_column_from_alias(prev_row_id, col)
                        cur_col = getattr(self.DBModel, col)
                        if order == 'asc':
                            col_cmp = prev_col < cur_col
                        else:
                            col_cmp = prev_col > cur_col
                        row_cmp = sqlalchemy.sql.or_(
                            col_cmp, 
                            sqlalchemy.sql.and_(prev_col == cur_col,
                                                row_cmp))
                    prev_row_id_query = sqlalchemy.sql.select([self.DBModel.get_column_from_alias(prev_row_id, 'id')], row_cmp)
                    for col, order in sort:
                        order = ['asc', 'desc'][order == 'asc'] # Sort backwards
                        prev_row_id_query = prev_row_id_query.order_by(
                            getattr(self.DBModel.get_column_from_alias(prev_row_id, col).expression_element(),
                                    order)())
                    prev_row_id_query = prev_row_id_query.limit(1)

                    # Now that previous line is outer joined to each line
                    prev_row = query.compile().alias()
                    query = query.select_from(
                        self.DBModel.table.outerjoin(
                            prev_row,
                            self.DBModel.get_column_from_alias(prev_row, 'id') == prev_row_id_query.as_scalar()))

                    # This should be recognizable from the pure in-memory
                    # algoritm used in Webwidgets.Table (it's nearly the
                    # same, but the loop has been unwound one time sort
                    # of, because it's easier to do it that way in SQL).
                    def tree_to_filter(node):
                        whens = []
                        for value, sub in node.values.iteritems():
                            sub_query = Worm.Utils.False_
                            if sub.toggled:
                                sub_query = tree_to_filter(sub)
                            whens.append((getattr(self.DBModel, node.col) == value,
                                         sub_query))
                        if whens:
                            node_query = sqlalchemy.sql.case(whens, else_ = Worm.Utils.False_)
                        else:
                            node_query = Worm.Utils.False_
                        return sqlalchemy.sql.case([(   self.DBModel.get_column_from_alias(prev_row, node.col)
                                                     == getattr(self.DBModel, node.col), node_query)],
                                                   else_ = Worm.Utils.True_)

                query = query.filter(tree_to_filter(expand_tree))

                for col, order in sort:
                    query = query.order_by(getattr(getattr(self.DBModel, col).expression_element(), order)())
                query = query.order_by(self.DBModel.id.asc())

                if not all:
                    query = query[(self.page - 1) * self.rows_per_page:
                                  self.page * self.rows_per_page]

                if self.debug_expand_info:
                    print "EXPAND"
                    print expand_tree
                if self.debug_queries:
                    print "QUERY"
                    print query

                return query

            def get_rows(self, all, output_options):
                return list(self.get_row_query(all, output_options))

            def get_row_by_id(self, row_id):
                return self.session.db.query(self.DBModel).filter(self.DBModel.id == row_id)[0]

            def get_row_id(self, row):
                return str(row.id)

            def get_pages(self):
                return int(math.ceil(float(self.get_row_query(True, {}).count()) / self.rows_per_page))

    class RowsFilters(Webwidgets.Table.RowsFilters):
        WwFilters = Webwidgets.Table.RowsFilters.WwFilters + ["StaticRowsFilter"]

        class StaticRowsFilter(Webwidgets.Filter):
            def get_rows(self, all, output_options):
                return self.pre_rows + self.ww_filter.get_rows(all, output_options) + self.post_rows

            def get_row_by_id(self, row_id):
                if row_id.startswith("pre_"):
                    return self.pre_rows[int(row_id[4:])]
                elif row_id.startswith("post_"):
                    return self.post_rows[int(row_id[5:])]
                else: # elif row_id.startswith("dyn_"):
                    return self.ww_filter.get_row_by_id(row_id[4:])
                
            def get_row_id(self, row):
                if row in self.pre_rows:
                    return "pre_%s" % (self.pre_rows.index(row),)
                elif row in self.post_rows:
                    return "post_%s" % (self.post_rows.index(row),)
                else:
                    return "dyn_%s" % (self.ww_filter.get_row_id(row),)

class Table(ReadonlyTable):
    class TableRowModelWrapper(ReadonlyTable.TableRowModelWrapper):
        WwFilters = ["EditingFilter"]

        class EditingFilter(Webwidgets.Filter):
            def __init__(self, *arg, **kw):
                Webwidgets.Filter.__init__(self, *arg, **kw)
                object.__setattr__(self, 'edit_widgets', {})
                if self.is_new():
                    self.edit()

            def is_new(self):
                return getattr(self, 'ww_is_new', False)

            def edit(self):
                if self.edit_widgets: return
                self.new_version = self.object.ww_model
                if not self.is_new():
                    self.new_version = self.new_version.copy()
                self.edit_widgets = self.new_version.get_column_input_widget_instances(self.table.session, self.table.win_id)
                
            def revert(self):
                self.edit_widgets = {}
                if self.is_new():
                    self.table.pre_rows.remove(self.object.ww_model)
                    
            def save(self):
                if not self.is_new():
                    self.object.is_current = False
                self.table.session.db.save(self.new_version)
                self.table.session.db.flush()
                self.table.session.db.commit()
                self.table.ww_filter.reread()
                self.revert()
                self.new_version.ww_is_new = False

            def delete(self):
                if self.is_new():
                    self.revert()
                else:
                    self.object.is_current = False
                    self.table.session.db.flush()
                    self.table.session.db.commit()
                    self.table.ww_filter.reread()

            def __getattr__(self, name):
                if name in self.edit_widgets:
                    return self.edit_widgets[name]
                return getattr(self.ww_filter, name)

    def function(self, path, function, row_id):
        row = self.ww_filter.get_row_by_id(row_id)
        if function == "edit":
            row.ww_filter.edit()
        elif function == "revert":
            row.ww_filter.revert()
        elif function == "save":
            row.ww_filter.save()
        elif function == "delete":
            row.ww_filter.delete()

    def group_function(self, path, function):
        if function == "new":
            self.pre_rows.append(self.DBModel(ww_is_new = True))
