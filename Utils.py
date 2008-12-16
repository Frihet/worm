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

import Webwidgets.Utils
import sqlalchemy, sqlalchemy.sql, sqlalchemy.orm

@Webwidgets.Utils.Cache.cache(per_request = True, per_class=True)
def load_all_from_session(session, instance):
    print "load_all_from_session"
    #### fixme ####
    # name = """SQLAlchemy: merge clashes with
    # many-to-many"""
    # description = """Uggly hack since merge does not
    # seem to work when you have many-to-many
    # relationships!!! So when no fields are changed, at
    # least you can do this instead..."""
    #### end ####
    t = type(instance)
    l = list(session.query(t))
    print "Load all", t, len(l)
    return l

def load_from_session_cached(session, instance):
    return filter(lambda item: item.id == instance.id, load_all_from_session(session, instance))[0]
    
