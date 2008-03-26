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
import Worm.Utils, math, sqlalchemy.sql, itertools

class Table(Webwidgets.Table):
    debug_queries = False
    debug_expand_info = False

    class Model(Webwidgets.Table.Model):
        class DBModel(object):
            def __getattr__(self, name):
                if name == "ww_row_id":
                    return self.id
                raise AttributeError

            def iterkeys(self):
                return itertools.imap(lambda col: col.name, type(self).table.columns)

            def iteritems(self):
                return itertools.imap(lambda name: (name, self[name]), self.iterkeys())

            def itervalues(self):
                return itertools.imap(lambda name: self[name], self.iterkeys())

            def __iter__(self):
                return self.iterkeys()

            def __getitem__(self, name):
                return getattr(self, name)

            def get(self, name, default = None):
                try:
                    return self[name]
                except AttributeError:
                    if default is not None:
                        return default
                    raise AttributeError
    
    class RowFilters(Webwidgets.Table.RowFilters):
        Filters = Webwidgets.Table.RowFilters.Filters + ['SQLAlchemyFilter']

    class SQLAlchemyFilter(Webwidgets.Filter):
        non_memory_storage = True

        def get_row_query(self, all, output_options):
            expand_tree = self.get_expand_tree()
            query = self.session.db.query(self.DBModel)

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
                        return self.DBModel.table.c.id.in_(node.rows.keys())
                    else:
                        whens = []
                        for value, sub in node.values.iteritems():
                            whens.append((getattr(self.DBModel.table.c, node.col) == value,
                                         tree_to_filter(sub)))
                        if whens:
                            return sqlalchemy.sql.case(whens, else_ = Worm.Utils.True_)
                        else:
                            return Worm.Utils.True_
            else:
                # OK, this is a bit uggly, but there is no other way in SQL :(
                # This computes the previous line (per the sorting order) of each line
                prev_row_id = self.DBModel.table.alias()
                row_cmp = Worm.Utils.False_
                for col, order in reversed(sort):
                    prev_col = getattr(prev_row_id.c, col)
                    cur_col = getattr(self.DBModel.table.c, col)
                    if order == 'asc':
                        col_cmp = prev_col < cur_col
                    else:
                        col_cmp = prev_col > cur_col
                    row_cmp = sqlalchemy.sql.or_(
                        col_cmp, 
                        sqlalchemy.sql.and_(prev_col == cur_col,
                                            row_cmp))
                prev_row_id_query = sqlalchemy.sql.select([prev_row_id.c.id], row_cmp)
                for col, order in sort:
                    order = ['asc', 'desc'][order == 'asc'] # Sort backwards
                    prev_row_id_query = prev_row_id_query.order_by(getattr(getattr(prev_row_id.c, col), order)())
                prev_row_id_query = prev_row_id_query.limit(1)

                # Now that previous line is outer joined to each line
                prev_row = self.DBModel.table.alias()
                query = query.select_from(
                    self.DBModel.table.outerjoin(
                        prev_row,
                        prev_row.c.id == prev_row_id_query.as_scalar()))

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
                        whens.append((getattr(self.DBModel.table.c, node.col) == value,
                                     sub_query))
                    if whens:
                        node_query = sqlalchemy.sql.case(whens, else_ = Worm.Utils.False_)
                    else:
                        node_query = Worm.Utils.False_
                    return sqlalchemy.sql.case([(getattr(prev_row.c, node.col) == getattr(self.DBModel.table.c, node.col), node_query)],
                                               else_ = Worm.Utils.True_)

            query = query.filter(tree_to_filter(expand_tree))

            for col, order in sort:
                query = query.order_by(getattr(getattr(self.DBModel.table.c, col), order)())
            query = query.order_by(self.DBModel.table.c.id.asc())

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
            return self.session.db.query(self.DBModel).filter(self.DBModel.table.c.id == row_id)[0]

        def get_row_id(self, row):
            return str(row['id'])

        def get_pages(self):
            return int(math.ceil(float(self.get_row_query(True, {}).count()) / self.rows_per_page))
