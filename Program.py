import Webwidgets

class Program(Webwidgets.Program):
    DBModel = None
    """Set this to the Model module of your application. It should
    have a module-level variable called engine assigned the result of
    a call to Worm.create_engine()."""
    
    class Session(Webwidgets.Program.Session):
        def __init__(self, *arg, **attrs):
            Webwidgets.Program.Session.__init__(self, *arg, **attrs)
            self.db = self.Program.DBModel.engine.Session()
