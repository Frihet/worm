#! /bin/env python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

# Lumbricidae Worm widget object relational mapper
# Copyright (C) 2008 Egil Moeller <egil.moeller@freecode.no>
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

# create_engine and View has been written by Egil in his spare-time
# for another project.

import sqlalchemy, sqlalchemy.sql, sqlalchemy.orm

True_ = sqlalchemy.sql.text("(1 = 1)")
False_ = sqlalchemy.sql.text("(1 = 2)")

def create_engine(url):
    engine = sqlalchemy.create_engine(url)
    engine.session_arguments = {'autoflush': True,
                                'transactional': True,
                                }
    def sessions(**kws):
        real_kws = {}
        real_kws.update(engine.session_arguments)
        real_kws.update(kws)
        BaseSession = sqlalchemy.orm.sessionmaker(bind=engine, **real_kws)
        class Session(BaseSession):
            def __enter__(self):
                return self

            def __exit__(self, type, value, traceback):
                if type is None and value is None and traceback is None:
                    self.commit()
                else:
                    self.rollback()
                self.close()

            def save(self, obj):
                BaseSession.save(self, obj)
                return  obj
                
            def expire(self, obj):
                BaseSession.expire(self, obj)
                return  obj
                
            def save_and_expire(self, obj):
                self.save(obj)
                self.flush()
                return self.expire(obj)
            
        return Session
    engine.sessions = sessions
    engine.Session = sessions()
    return engine

class View(sqlalchemy.sql.expression.TableClause, sqlalchemy.schema.SchemaItem):
    __visit_name__ = 'table'

    def __init__(self, name, metadata, expression, primary_key = 'id', **kw):
        self._expression = expression
        metadata.append_ddl_listener('after-create', self.create)
        metadata.append_ddl_listener('before-drop', self.drop)
        sqlalchemy.sql.expression.TableClause.__init__(self, name, *self._expression.columns, **kw)
        if isinstance(primary_key, str):
            primary_key = sqlalchemy.sql.expression.ColumnCollection(self._expression.columns[primary_key])
	self._primary_key = primary_key

    def create(self, event, metadata, bind):
        try:
            self.drop(event, metadata, bind)
        except:
            pass
        
        select =self._expression.compile(bind = bind)
        params = select.construct_params()
        sqlalchemy.schema.DDL("create view %(name)s as %(select)s" %
                              {'name': self.name,
                               'select': select},
                              context=params).execute(bind)
                              
    def drop(self, event, metadata, bind):
        sqlalchemy.schema.DDL("drop view %(name)s" %
                              {'name': self.name}).execute(bind)
