import Webwidgets
import sqlalchemy

class BaseModel(object):
    """This class extends SQLAlchemy models with some extra utility
    methods, and provides widgets for editing the database fields of
    the model."""

    def __unicode__(self):
        if hasattr(self, 'title'):
            return unicode(self.title)
        return repr(self)

    def __str__(self):
        return str(unicode(self))    

    def __repr__(self):
        return "<%s.%s%s>" % (type(self).__module__, type(self).__name__,
                              ','.join(["\n %s=%s" % (name, unicode(getattr(self, name)))
                                        for name in self.get_column_names()]))
        
    def get_columns(cls, exclude_primary_keys = False, exclude_foreign_keys = False):
        return [(name, col)
                for (name, col) in [(name, getattr(cls, name))
                                    for name in dir(cls)]
                if (# Filter out non-column attributes
                        hasattr(col, 'impl')
                    and isinstance(col.impl, sqlalchemy.orm.attributes.AttributeImpl)

                    # Filter out primary and foreign keys, if requested
                    and not (isinstance(col.comparator.prop, sqlalchemy.orm.properties.ColumnProperty)
                             and col.comparator.prop.columns
                             and (   (exclude_foreign_keys and col.comparator.prop.columns[0].foreign_keys)
                                  or (exclude_primary_keys and col.comparator.prop.columns[0].primary_key))))]
    get_columns = classmethod(get_columns)

    def get_columns_and_instances(self, *arg, **kw):
        return [(name, col, getattr(self, name))
                for (name, col) in self.get_columns(*arg, **kw)]

    def get_column_instances(self, *arg, **kw):
        return [(name, value)
                for (name, col, value) in self.get_columns_and_instances(*arg, **kw)]

    def get_column_names(cls, *arg, **kw):
        return [name
                for (name, col) in cls.get_columns(*arg, **kw)]
    get_column_names = classmethod(get_column_names)


    def column_is_scalar(cls, name):
        cls_member = getattr(cls, name)
        return isinstance(cls_member.impl, (sqlalchemy.orm.attributes.ScalarAttributeImpl,
                                            sqlalchemy.orm.attributes.ScalarObjectAttributeImpl))
    column_is_scalar = classmethod(column_is_scalar)

    def column_is_foreign(cls, name):
        cls_member = getattr(cls, name)
        return isinstance(cls_member.impl, (sqlalchemy.orm.attributes.ScalarObjectAttributeImpl,
                                            sqlalchemy.orm.attributes.CollectionAttributeImpl))
    column_is_foreign = classmethod(column_is_foreign)

    def get_column_subtype(cls, name):
        cls_member = getattr(cls, name)
        # Yes, this sucks, it is icky, but it's the only way to get at it
        # :(
        return cls_member.impl.is_equal.im_self
    get_column_subtype = classmethod(get_column_subtype)

    def get_column_foreign_class(cls, name):
        """This fetches the foreign key-pointed-to class for a column
        given the class member. The class member should be of one of the
        two types sqlalchemy.orm.attributes.ScalarObjectAttributeImpl and
        sqlalchemy.orm.attributes.CollectionAttributeImpl"""
        cls_member = getattr(cls, name)
        # Yes, this sucks, it is icky, but it's the only way to get at it
        # :(
        return cls_member.impl.callable_.im_self.mapper.class_
    get_column_foreign_class = classmethod(get_column_foreign_class)

    def get_column_foreign_column(cls, name):
        cls_member = getattr(cls, name)
        for ext in cls_member.impl.extensions:
            if isinstance(ext, sqlalchemy.orm.attributes.GenericBackrefExtension):
                return ext.key
        raise Exception("Column does not have a back-ref column in foreign table")
    get_column_foreign_column = classmethod(get_column_foreign_column)

    def get_column_input_widget(cls, name):
        if cls.column_is_foreign(name):
            if cls.column_is_scalar(name):
                return None
            else:
                return None
        else:
            if cls.column_is_scalar(name):
                subtype = cls.get_column_subtype(name)
                if isinstance(subtype, sqlalchemy.types.Boolean):
                    return Webwidgets.Checkbox
                elif isinstance(subtype, sqlalchemy.types.Unicode):
                    return Webwidgets.StringInput
                elif isinstance(subtype, sqlalchemy.types.String):
                    return Webwidgets.StringInput
                elif isinstance(subtype, sqlalchemy.types.DateTime):
                    return Webwidgets.DateInput
                elif isinstance(subtype, sqlalchemy.types.Date):
                    return Webwidgets.DateInput
                elif isinstance(subtype, sqlalchemy.types.Integer):
                    return Webwidgets.IntegerInput
                elif isinstance(subtype, sqlalchemy.types.Float):
                    return Webwidgets.FloatInput
            else:
                return None
    get_column_input_widget = classmethod(get_column_input_widget)

    def get_column_input_widgets(cls):
        return dict([(name, widget)
                     for (name, widget) in [(name, cls.get_column_input_widget(name))
                                            for name in
                                            cls.get_column_names()]
                     if widget is not None])
    get_column_input_widgets = classmethod(get_column_input_widgets)


    def get_column_input_widget_instance(self, session, win_id, name):
        widget = self.get_column_input_widget(name)
        if widget is None: return None
        return widget(session, win_id,
                      ww_model = Webwidgets.RenameWrapper(name_map = {'value': name},
                                                          ww_model = self).ww_filter)    

    def get_column_input_widget_instances(self, session, win_id):
        return dict([(name, self.get_column_input_widget_instance(session, win_id, name))
                     for name in self.get_column_names()])


    def copy(self, override = {}, copy_foreign = True):
        res = {}
        for name, value in self.get_column_instances(exclude_primary_keys = True,
                                                     exclude_foreign_keys = True):
            if name in override:
                res[name] = override[name]
            else:
                if self.column_is_foreign(name) and not self.column_is_scalar(name):
                    if copy_foreign:
                        res[name] = [foreign.copy(override = {self.get_column_foreign_column(name):None})
                                     for foreign in value]
                    else:
                        res[name] = []
                else:
                    res[name] = value
        return type(self)(**res)
