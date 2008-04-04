import Webwidgets

class DBFieldEditor(Webwidgets.ValueInput):
    def __init__(self, *arg, **kw):
        super(DBFieldEditor, self).__init__(*arg, **kw)
        self.value = getattr(self.row, self.name)
        
    def save(self):
        setattr(self.row, self.name, self.value)
