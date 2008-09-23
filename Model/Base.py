import Webwidgets, Argentum
import sqlalchemy

class BaseModel(Argentum.BaseModel):
    """This class extends SQLAlchemy models with some extra utility
    methods, and provides widgets for editing the database fields of
    the model."""

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
                    if value is None: return None
                    return instance.db_session.merge(value)
                def __set__(self, instance, value):
                    if value is not None:
                        value = instance.db_session.merge(value)
                    setattr(model, name, value)
        else:
            class Value(object):
                def __get__(self, instance, owner):
                    return getattr(model, name)
                def __set__(self, instance, value):
                    setattr(model, name, value)

        ValueMappedWidget = type("ValueMapped(%s.%s)" % (widget.__module__, widget.__name__),
                                 (widget,) + extra_classes,
                                 {'WwFilters': widget.WwFilters + ["ValueMappedWidgetValueMapper"],
                                  'ValueMappedWidgetValueMapper': type("ValueMappedWidgetValueMapper",
                                                                       (Webwidgets.Filter,),
                                                                       {'value': Value()})})

        class ValidatingValueMappedWidget(ValueMappedWidget):
            def validate(self):
                return getattr(model, "validate_%s" % (name, ), lambda x: True)(self.ww_filter.value)

        # Wrap widget in a composite widget with label
        class WidgetLabel(Webwidgets.Label):
            class Label(Webwidgets.Html):
                html = ''

        widget = ValidatingValueMappedWidget(session, win_id)
        label = WidgetLabel(session, win_id, target=widget)
        return Webwidgets.List(session, win_id, children={'Label': label, 'Widget': widget})

    def get_column_input_widget_instances(self, db_session, session, win_id, *extra_classes):
        return dict([(name, self.get_column_input_widget_instance(db_session, session, win_id, name, *extra_classes))
                     for name in self.get_column_names()])

