import Webwidgets

class Widget(Webwidgets.Widget):
    class DbSession(object):
        db_session = None
        def __get__(self, owner, instance, name):
            if self.db_session is not None:
                return self.db_session
            return self.session.db

        def __set__(self, instance, value):
            self.db_session = value

    
