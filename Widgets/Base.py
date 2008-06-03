import Webwidgets, sqlalchemy, sys

class Widget(Webwidgets.Widget):
    class DbSession(object):
        def __get__(self, instance, owner):
            try:
                if instance is None:
                    return None
                elif 'db_session' in instance.__dict__:
                    return instance.__dict__['db_session']
                elif hasattr(instance.ww_model, 'db_session'):
                    return instance.ww_model.db_session
                elif instance.parent is not None:
                    try:
                        return instance.parent.get_ansestor_by_attribute(name="db_session").db_session
                    except KeyError:
                        pass
                return instance.session.db
            except:
                import pdb
                sys.last_traceback = sys.exc_info()[2]
                pdb.pm()

        def __set__(self, instance, value):
            instance.__dict__['db_session'] = value

        def __delete__(self, instance):
            if instance.__dict__['db_session']:
                instance.__dict__['db_session'].close()
            del instance.__dict__['db_session']
            
    db_session = DbSession()

    def db_session_localize(self):
        self.db_session = self.db_session.bind.Session()

    def db_session_commit_and_globalize(self):
        self.db_session.commit()
        del self.db_session

    def db_session_rollback_and_globalize(self):
        del self.db_session

    def append_exception(self):
        if isinstance(sys.exc_info()[1], sqlalchemy.exceptions.SQLAlchemyError):
            self.db_session.rollback()
        Webwidgets.Widget.append_exception(self)
