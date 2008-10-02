import Webwidgets

class Program(Webwidgets.Program):
    DBModel = None
    """Set this to the Model module of your application. It should
    have a module-level variable called engine assigned the result of
    a call to Worm.create_engine()."""
