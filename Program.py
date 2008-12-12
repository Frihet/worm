import Webwidgets, Argentum

class Program(Webwidgets.Program):
    DBModel = None
    """Set this to the Model module of your application. It should
    have a module-level variable called engine assigned the result of
    a call to Worm.create_engine()."""

    class Session(Webwidgets.Program.Session):
        def __init__(self, *arg, **kw):
            Webwidgets.Program.Session.__init__(self, *arg, **kw)

            self.worm_localized = set()
            """Set of localized database sessions for cleanup."""

        def handle_request(self, transaction):
            Argentum.soil_all_pseudo_materialized()

            Webwidgets.Program.Session.handle_request(self, transaction)
