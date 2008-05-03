import Webwidgets

# FXIME: Shouldn't this use Webwidgets.RenameWrapper?
class DBFieldEditor(Webwidgets.ValueInput):
    WwFilters = ['RenameFilter']
    
    class RenameFilter(Webwidgets.Filter):
        def __getattr__(self, name):
            #print "GETATTR %s -> %s:%s" % (name, self.object.ww_model, self.ww_filter.name_map.get(name, name))
            return getattr(self.ww_filter, self.ww_filter.name_map.get(name, name))
            
        def __setattr__(self, name, value):
            #print "SETATTR %s -> %s:%s = %s" % (name, self.object.ww_model, self.ww_filter.name_map.get(name, name), value)
            setattr(self.ww_filter, self.ww_filter.name_map.get(name, name), value)
