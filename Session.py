from __future__ import with_statement
import sqlalchemy, Argentum, Webwidgets

BaseConnection = sqlalchemy.engine.base.Connection
class Connection(BaseConnection):
    def execute(self, *arg, **kw):
        try:
            timings = Webwidgets.Program.transaction().request().timings
        except AttributeError:
            return BaseConnection.execute(self, *arg, **kw)
        else:
            sql = arg[0]
            if not isinstance(sql, (str, unicode)):
                sql = sql.compile(self)
                params = sql.construct_params()
                sql = str(sql)
                for key, value in params.iteritems():
                    sql = sql.replace(":%s" % (key,),
                                      "'%s'" % (value,))
                
            with timings('sql', sql):
                return BaseConnection.execute(self, *arg, **kw)

sqlalchemy.engine.base.Connection = Connection


def create_engine(url):
    return Argentum.create_engine(url)
