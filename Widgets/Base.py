import Webwidgets, sqlalchemy, sys

class Widget(Webwidgets.Widget):
    """Base class for all widgets that interact with SQLAlchemy,
    providing methods for managing SQLAlchemy sessions."""
    
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
            if 'db_session' not in instance.__dict__: return
            if instance.__dict__['db_session']:
                instance.__dict__['db_session'].close()
            del instance.__dict__['db_session']
            
    db_session = DbSession()
    """The current SQLAlchemy session, used along the lines of
    C{self.db_session.query(Some.DBMappedClass).filter(...)}."""

    def db_session_is_localized(self):
        """Return True if session is localized."""
        return self.__dict__.has_key('db_session')

    def db_session_localize(self):
        """Open a new SQLAlchemy session. This new session is assigned
        to L{db_session} of this widget and all descendant widgets
        until either L{db_session_commit_and_globalize} or
        L{db_session_rollback_and_globalize} is called on this widget.

        Note: You should not call this method more than once without
        an intervening call to either rollback or commit.
        """
        self.db_session = self.db_session.bind.Session()

    def db_session_commit_and_globalize(self):
        """Commit the current local SQLAlchemy session (created with
        L{db_session_localize} on this widget) and remove/close the
        session, making the global session visible to this widget and
        descendant widgets again. You might want to do
        self.db_session.expire() after this to make any changes to
        your local session visible in the global session (to this and
        other widgets)."""
        self.db_session.commit()
        del self.db_session
        # FIXME: Update all nested localized sessions.
        self.db_session.expire_all()

    def db_session_rollback_and_globalize(self):
        """Rollback the current local SQLAlchemy session (created with
        L{db_session_localize} on this widget) and remove/close the
        session, making the global session visible to this widget and
        descendant widgets again."""
        self.db_session.rollback()
        del self.db_session

    def append_exception(self, message=u''):
        """Rollbacks the current (local) SQLAlchemy session and
        appends the current exception and backtrace to the list of
        error messages for this widget.""" 
        if isinstance(sys.exc_info()[1], sqlalchemy.exceptions.SQLAlchemyError):
            self.db_session.rollback()
        Webwidgets.Widget.append_exception(self, message)
