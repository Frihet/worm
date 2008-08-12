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
import Argentum, Worm.Model.Base, Worm.Widgets.Base, math, sqlalchemy.sql, itertools, types

class RowsComposite(Webwidgets.RowsComposite, Worm.Widgets.Base.Widget):
    """This is a version of L{RowsComposite} that fetches the rows
    from an SQLAlchemy mapped class."""
    
    debug_queries = False
    debug_expand_info = False
    debug_rows = False

    class WwModel(Webwidgets.RowsComposite.WwModel):
        db_where = None
        """This is a filter to be applied to all database queries,
        prior to any sorting, expansion etc. It can be any SQLAlchemy
        SQL Expression expression."""
        db_mangle = None
        """This method is called with the current query and should
        return an mangled version of the query."""

        class DBModel(Worm.Model.Base.BaseModel):
            """This is the database model used by the model. This
            class must be subclassed and mapped using SQLAlchemy. It
            requires the mapped model class to be available in the
            table attribute (this is fullfilled automatically if you
            are using elixir)."""
            
            def __getattr__(self, name):
                if name == "ww_row_id":
                    return self.id
                raise AttributeError(self, name)
            def get_column_from_alias(cls, alias, col):
                new_col = "%s_%s" % (cls.table.name, col)
                if hasattr(alias.c, new_col):
                    return getattr(alias.c, new_col)
                else:
                    return getattr(alias.c, col)
            get_column_from_alias = classmethod(get_column_from_alias)

        pre_rows = []
        post_rows = []

        def __init__(self):
            super(RowsComposite.WwModel, self).__init__()
            self.pre_rows = list(self.pre_rows)
            self.post_rows = list(self.post_rows)
    
    class SourceFilters(Webwidgets.RowsComposite.SourceFilters):
        WwFilters = Webwidgets.RowsComposite.SourceFilters.WwFilters + ['SQLAlchemyFilter']

        class SQLAlchemyFilter(Webwidgets.Filter):
            """This filter provides rows from an SQLAlchemy back-end,
            compiling sorting and the row collapse/expand code into
            SQLExpression."""
            
            non_memory_storage = True

            def get_row_query(self, all = False, output_options = {}, **kw):
                expand_tree = self.get_expand_tree()
                query = self.db_session.query(self.DBModel)
                if self.db_where is not None:
                    query = query.filter(self.db_where)
                if self.db_mangle is not None:
                    query = self.db_mangle(query)

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
                            return self.DBModel.id.in_([
                                self.object.ww_filter.get_row_id_to_model_row_id(key)
                                for key in node.rows.keys()])
                        else:
                            whens = []
                            for value, sub in node.values.iteritems():
                                whens.append((getattr(self.DBModel, node.col) == value,
                                             tree_to_filter(sub)))
                            if whens:
                                return sqlalchemy.sql.case(whens, else_ = Argentum.True_)
                            else:
                                return Argentum.TrueWhere
                else:
                    # OK, this is a bit uggly, but there is no other way in SQL :(
                    # This computes the previous line (per the sorting order) of each line
                    prev_row_id = query.compile().alias()
                    row_cmp = Argentum.False_
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
                            sub_query = Argentum.False_
                            if sub.toggled:
                                sub_query = tree_to_filter(sub)
                            whens.append((getattr(self.DBModel, node.col) == value,
                                         sub_query))
                        if whens:
                            node_query = sqlalchemy.sql.case(whens, else_ = Argentum.False_)
                        else:
                            node_query = Argentum.FalseWhere
                        return sqlalchemy.sql.case([(   self.DBModel.get_column_from_alias(prev_row, node.col)
                                                     == getattr(self.DBModel, node.col), node_query)],
                                                   else_ = Argentum.True_)
                query = query.filter(tree_to_filter(expand_tree))

                for col, order in sort:
                    if self.DBModel.column_is_foreign(col):
                        # FIXME: WHat if we have multiple foreign keys to the same table?
                        query = query.filter(self.DBModel.get_column_primary_join(col))
                        col = self.DBModel.get_column_foreign_class(col).table.c.title
                    else:
                        # FIXME: Explain why we do this
                        col = getattr(self.DBModel, col).expression_element()
                    query = query.order_by(getattr(col, order)())
                query = query.order_by(self.DBModel.id.asc())

                if not all and self.rows_per_page != 0:
                    query = query[(self.page - 1) * self.rows_per_page:
                                  self.page * self.rows_per_page]

                if self.debug_expand_info:
                    print "EXPAND"
                    print expand_tree
                if self.debug_queries:
                    print "QUERY"
                    print query

                return query

            def get_rows(self, **kw):
                result = list(self.get_row_query(**kw))
                if self.debug_rows:
                    print "ROWS", repr(self), "==>"
                    for row in result:
                        print "    ", repr(row)
                        print "   ==>", 
                return result

            def get_row_by_id(self, row_id, **kwargs):
                return self.db_session.query(self.DBModel).filter(self.DBModel.id == int(row_id))[0]

            def get_row_id(self, row):
                return str(row.id)

            def get_pages(self):
                return int(math.ceil(float(self.get_row_query(all = True).count()) / self.rows_per_page))

    class RowsFilters(Webwidgets.RowsComposite.RowsFilters):
        WwFilters = Webwidgets.RowsComposite.RowsFilters.WwFilters + ["StaticRowsFilter"]

        class StaticRowsFilter(Webwidgets.Filter):
            """This filters prepends and appends rows from L{pre_rows}
            and L{post_rows} respectively to the rows returned by
            SQLAlchemy."""
            
            def get_rows(self, **kw):
                return self.pre_rows + self.ww_filter.get_rows(**kw) + self.post_rows

            def get_row_by_id(self, row_id, **kwargs):
                if row_id.startswith("pre_"):
                    return self.pre_rows[int(row_id[4:])]
                elif row_id.startswith("post_"):
                    return self.post_rows[int(row_id[5:])]
                elif row_id.startswith("dyn_"):
                    return self.ww_filter.get_row_by_id(row_id[4:], **kwargs)
                raise Exception("Invalid row-id %s (should have started with 'pre_', 'post_' or 'dyn_')" % row_id)
                
            def get_row_id(self, row):
                if row in self.pre_rows:
                    return "pre_%s" % (self.pre_rows.index(row),)
                elif row in self.post_rows:
                    return "post_%s" % (self.post_rows.index(row),)
                else:
                    return "dyn_%s" % (self.ww_filter.get_row_id(row),)
