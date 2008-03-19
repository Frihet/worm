#! /usr/bin/env python2.5

from __future__ import with_statement

import sqlalchemy, sqlalchemy.orm, elixir, sys
import Webwidgets.Demo.TableAutoexpandORM.Model
import Webwidgets.Demo.TableAutoexpandORM.Database


kws = dict([arg[2:].split('=', 1)
            for arg in sys.argv[1:]
            if arg.startswith('--') and '=' in arg])
options = set([arg[2:]
               for arg in sys.argv[1:]
               if arg.startswith('--') and '=' not in arg])
files = [arg
         for arg in sys.argv[1:]
         if not arg.startswith('--')]


if 'drop' in options:
    elixir.drop_all(bind=Webwidgets.Demo.TableAutoexpandORM.Database.engine)

if 'schema' in options or 'all' in options:
    elixir.create_all(bind=Webwidgets.Demo.TableAutoexpandORM.Database.engine)

if 'data' in options or 'all' in options:
    with Webwidgets.Demo.TableAutoexpandORM.Database.engine.Session() as session:
        Webwidgets.Demo.TableAutoexpandORM.Model.createInitialData(session)
