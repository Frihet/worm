import Webwidgets, Argentum
import sqlalchemy

class BaseModel(Argentum.BaseModel):
    """This class extends SQLAlchemy models with some extra utility
    methods, and provides widgets for editing the database fields of
    the model.

    Such input widgets provides validators taken from the model. There
    are two types of validators a model can provide - column specific
    and generic ones.

    The column-specific ones are specified as

    invalid_COLUMNNAME_something_went_wrong = "Something went terribly wrong..."
    def validate_COLUMNNAME_something_went_wrong(self):
        return True or False

    while the generic ones are specified as
    
    invalid_all_something_went_wrong = "Something went terribly wrong..."
    def validate_all_something_went_wrong(self, column_name):
        return True or False
    """

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


    def get_column_input_widget_instance(self, db_session, session, win_id, name, *extra_classes):
        import Worm.Widgets.ListMod
        model = self
        widget = self.get_column_input_widget(name)
        if widget is None: return None

        if issubclass(widget, Worm.Widgets.ListMod.RowsSingleValueListInput):
            class Value(object):
                def __get__(self, instance, owner):
                    if instance is None: return None

                    value = getattr(model, name)
                    if value is not None:
                        value = db_session.load_from_session(value)
                    return value

                def __set__(self, instance, value):
                    if value is not None:
                        value = db_session.load_from_session(value)
                    setattr(model, name, value)
        else:
            class Value(object):
                def __get__(self, instance, owner):
                    return getattr(model, name)
                def __set__(self, instance, value):
                    setattr(model, name, value)        

        members = {'WwFilters': widget.WwFilters + ["ValueMappedWidgetValueMapper"],
                   'ValueMappedWidgetValueMapper': type("ValueMappedWidgetValueMapper",
                                                        (Webwidgets.Filter,),
                                                        {'value': Value()})}
        # Set up validators
        def split_name(member_name):
            for member_type in ["validate_", "invalid_"]:
                if member_name.startswith(member_type):
                    member_name = member_name[len(member_type):]
                    for member_scope in ["all_", name + "_"]:
                        if member_name.startswith(member_scope):
                            return member_type, member_scope, member_name[len(member_scope):]
            return None
        for member_name in dir(model):
            split_member_name = split_name(member_name)
            if not split_member_name: continue
            member_type, member_scope, split_member_name = split_member_name

            member_value = getattr(model, member_name)
            if member_type == "validate_":
                def make_method(member_scope, member_value, name):
                    if member_scope == "all_":
                        return lambda self: member_value(name)
                    else:
                        return lambda self: member_value()
                members['validate_' + split_member_name] = make_method(member_scope, member_value, name)
            else:
                members['invalid_' + split_member_name] = member_value

        ValueMappedWidget = type("ValueMapped(%s.%s)" % (widget.__module__, widget.__name__),
                                 (widget,) + extra_classes,
                                 members)

        # Wrap widget in a composite widget with label
        return Webwidgets.Field(session, win_id,
                                children={'Label': Webwidgets.Html(session, win_id, html=''),
                                          'Field': ValueMappedWidget(session, win_id)})

    def get_column_input_widget_instances(self, db_session, session, win_id, *extra_classes):
        return dict([(name, self.get_column_input_widget_instance(db_session, session, win_id, name, *extra_classes))
                     for name in self.get_column_names()])

    invalid_all_not_empty = "Field can not be empty"
    def validate_all_not_empty(self, col):
        return not getattr(self, "%s__not_empty" % (col,), False) or not not getattr(self, col)
