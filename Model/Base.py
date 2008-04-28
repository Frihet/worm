import Webwidgets
import sqlalchemy

class BaseModel(object):
    """This class extends SQLAlchemy models with some extra utility
    methods, and provides widgets for editing the database fields of
    the model."""

    def __unicode__(self):
        if hasattr(self, 'title'):
            return unicode(self.title)
        if hasattr(self, 'id'):
            return "%s.%s %s" % (type(self).__module__, type(self).__name__, self.id)
        return "%s.%s" % (type(self).__module__, type(self).__name__)

    def __str__(self):
        return str(unicode(self))    

    def __repr__(self):
        def strattr(name):
            value = getattr(self, name)
            if self.column_is_scalar(name):
                return unicode(value)
            else:
                return ', '.join(unicode(part) for part in value)
        return "<%s.%s%s>" % (type(self).__module__, type(self).__name__,
                              ','.join(["\n %s=%s" % (name, strattr(name))
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
        # We can't import this globally, or we'd have a loop in import dependenmcies :S
        import Worm.Widgets.ListMod

        if cls.column_is_foreign(name):
            if cls.column_is_scalar(name):
                foreign = cls.get_column_foreign_class(name)
                class ForeignInput(Worm.Widgets.ListMod.RowsSingleValueListInput):
                    class WwModel(Worm.Widgets.ListMod.RowsSingleValueListInput.WwModel):
                        DBModel = foreign
                        if hasattr(foreign, 'is_current'):
                            db_where = foreign.is_current == True
                return ForeignInput
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


    def get_column_input_widget_instance(self, db_session, session, win_id, name):
        import Worm.Widgets.ListMod
        model = self
        widget = self.get_column_input_widget(name)
        if widget is None: return None

        if issubclass(widget, Worm.Widgets.ListMod.RowsSingleValueListInput):
            class Value(object):
                def __get__(self, instance, owner):
                    value = getattr(model, name)
                    if value is None: return None
                    return instance.db_session.merge(value)
                def __set__(self, instance, value):
                    if value is not None:
                        value = db_session.merge(value)
                    setattr(model, name, value)
        else:
            class Value(object):
                def __get__(self, instance, owner):
                    return getattr(model, name)
                def __set__(self, instance, value):
                    setattr(model, name, value)

        class ValueMappedWidget(widget):
            WwFilters = widget.WwFilters + ["ValueMappedWidgetValueMapper"]
            class ValueMappedWidgetValueMapper(Webwidgets.Filter):
                value = Value()
                
        return ValueMappedWidget(session, win_id)    

    def get_column_input_widget_instances(self, db_session, session, win_id):
        return dict([(name, self.get_column_input_widget_instance(db_session, session, win_id, name))
                     for name in self.get_column_names()])


    def copy(self, override = {}, copy_foreign = True):
        res = {}
        for name, value in self.get_column_instances(exclude_primary_keys = True,
                                                     exclude_foreign_keys = True):
            if name in override:
                res[name] = override[name]
            else:
                if self.column_is_foreign(name):
                    foreign_name = self.get_column_foreign_column(name)
                    if self.column_is_scalar(name):
                        res[name] = value
                        if getattr(self, name + '__ww_copy_foregin', False):
                            if copy_foreign:
                                foreign_col = list(getattr(value, foreign_name))
                                foreign_col.remove(self)
                                res[name] = value.copy(override = {foreign_name:foreign_col})
                                if hasattr(value, "is_current"):
                                    value.is_current = False
                    else:
                        res[name] = []
                        if self.get_column_foreign_class(name).column_is_scalar(foreign_name):
                            if copy_foreign:
                                for foreign in value:
                                    res[name].append(foreign.copy(override = {foreign_name:None}))
                                    if hasattr(foreign, "is_current"):
                                        foreign.is_current = False
                        elif getattr(self, name + '__ww_copy_foregin', False):
                            if copy_foreign:
                                for foreign in value:
                                    foreign_col = list(getattr(foreign, foreign_name))
                                    foreign_col.remove(self)
                                    res[name].append(foreign.copy(override = {foreign_name:foreign_col}))
                                    if hasattr(foreign, "is_current"):
                                        foreign.is_current = False
                else:
                    res[name] = value
        return type(self)(**res)
