#! /usr/bin/env python2.5

from __future__ import with_statement

import sqlalchemy, sqlalchemy.orm, elixir, sys


kws = dict([arg[2:].split('=', 1)
            for arg in sys.argv[1:]
            if arg.startswith('--') and '=' in arg])
options = set([arg[2:]
               for arg in sys.argv[1:]
               if arg.startswith('--') and '=' not in arg])
files = [arg
         for arg in sys.argv[1:]
         if not arg.startswith('--')]

if 'help' in options:
    print """Usage: SetupDatabase.py --model=ORM.Model.Python.Module.Path OPTIONS
    Where OPTIONS are
        --drop
            Drop all database objects (tables, views etc). ALL DATA WILL BE LOST!
        --all
            Equivalent to --schema and --data
        --schema
            Create all tables and views
        --data
            Insert initial data into tables
"""
    sys.exit(0)

model = __import__(kws['model'])
for item in kws['model'].split('.')[1:]:
    model = getattr(model, item)

if 'drop' in options:
    elixir.drop_all(bind=model.engine)

if 'schema' in options or 'all' in options:
    elixir.create_all(bind=model.engine)

if 'data' in options or 'all' in options:
    with model.engine.Session() as session:
        model.createInitialData(session)
