import Webwidgets
import Worm.Widgets.Input, sqlalchemy

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
                                        for (name, col) in self.get_columns().iteritems()]))
        
    def get_columns(cls):
        return dict([(key, col)
                     for (key, col) in [(key, getattr(cls, key))
                                        for key in dir(cls)]
                     if hasattr(col, 'impl') and isinstance(col.impl, sqlalchemy.orm.attributes.AttributeImpl)])
    get_columns = classmethod(get_columns)

    def column_is_scalar(cls, cls_member):
        return isinstance(cls_member.impl, (sqlalchemy.orm.attributes.ScalarAttributeImpl,
                                            sqlalchemy.orm.attributes.ScalarObjectAttributeImpl))
    column_is_scalar = classmethod(column_is_scalar)

    def column_is_foreign(cls, cls_member):
        return isinstance(cls_member.impl, (sqlalchemy.orm.attributes.ScalarObjectAttributeImpl,
                                            sqlalchemy.orm.attributes.CollectionAttributeImpl))
    column_is_foreign = classmethod(column_is_foreign)

    def get_column_subtype(cls, cls_member):
        # Yes, this sucks, it is icky, but it's the only way to get at it
        # :(
        return cls_member.impl.is_equal.im_self
    get_column_subtype = classmethod(get_column_subtype)

    def get_column_foreign_class(cls, cls_member):
        """This fetches the foreign key-pointed-to class for a column
        given the class member. The class member should be of one of the
        two types sqlalchemy.orm.attributes.ScalarObjectAttributeImpl and
        sqlalchemy.orm.attributes.CollectionAttributeImpl"""
        # Yes, this sucks, it is icky, but it's the only way to get at it
        # :(
        return cls_member.impl.callable_.im_self.mapper.class_
    get_column_foreign_class = classmethod(get_column_foreign_class)

    def get_column_input_widget(cls, cls_member):
        if cls.column_is_foreign(cls_member):
            if cls.column_is_scalar(cls_member):
                return None
            else:
                return None
        else:
            if cls.column_is_scalar(cls_member):
                subtype = cls.get_column_subtype(cls_member)
                if isinstance(subtype, sqlalchemy.types.Boolean):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.Checkbox)
                elif isinstance(subtype, sqlalchemy.types.Unicode):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.StringInput)
                elif isinstance(subtype, sqlalchemy.types.String):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.StringInput)
                elif isinstance(subtype, sqlalchemy.types.DateTime):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.DateInput)
                elif isinstance(subtype, sqlalchemy.types.Date):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.DateInput)
                elif isinstance(subtype, sqlalchemy.types.Integer):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.IntegerInput)
                elif isinstance(subtype, sqlalchemy.types.Float):
                    return Worm.Widgets.Input.DBFieldEditor.derive(Webwidgets.FloatInput)
            else:
                return None
    get_column_input_widget = classmethod(get_column_input_widget)

    def get_column_input_widgets(cls):
        return dict([(name, widget)
                     for (name, widget) in [(key, cls.get_column_input_widget(col))
                                            for (key, col) in
                                            cls.get_columns().iteritems()]
                     if widget is not None])
    get_column_input_widgets = classmethod(get_column_input_widgets)

    def get_column_input_widget_instances(self, session, win_id):
        return dict([(name, widget(session, win_id,
                                   name_map = {'value': name},
                                   ww_model = self))
                     for (name, widget) in self.get_column_input_widgets().iteritems()])
    
    def copy(self):
        return type(self)(**dict([(name, getattr(self, name))
                                  for (name, col) in self.get_columns().iteritems()
                                  if not (    isinstance(col.comparator.prop, sqlalchemy.orm.properties.ColumnProperty)
                                          and col.comparator.prop.columns
                                           and (   col.comparator.prop.columns[0].foreign_keys
                                                or col.comparator.prop.columns[0].primary_key))]))
