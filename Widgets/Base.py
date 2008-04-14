import Webwidgets

class Widget(Webwidgets.Widget):
    _db_session = None
    class DbSession(object):
        def __get__(self, instance, owner):
            if instance._db_session is not None:
                return instance._db_session
            return instance.session.db

        def __set__(self, instance, value):
            instance._db_session = value

        def __delete__(self, instance):
            if instance._db_session is not None:
                instance._db_session.close()
            instance._db_session = None
            
    db_session = DbSession()
    
    def db_session_localize(self):
        self.db_session = self.db_session.bind.Session()

    def db_session_commit_and_globalize(self):
        self.db_session.commit()
        del self.db_session

    def db_session_rollback_and_globalize(self):
        del self.db_session
