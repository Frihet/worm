import elixir, itertools

__session__ = None

class Service(elixir.entity.Entity):
    country = elixir.Field(elixir.Unicode)
    provider = elixir.Field(elixir.Unicode)
    technology = elixir.Field(elixir.Unicode)
    price = elixir.Field(elixir.Unicode)

    def __getattr__(self, name):
        if name == "ww_row_id":
            return self.id
        raise AttributeError

    def iterkeys(self):
        return itertools.imap(lambda col: col.name, type(self).table.columns)

    def iteritems(self):
        return itertools.imap(lambda name: (name, self[name]), self.iterkeys())

    def itervalues(self):
        return itertools.imap(lambda name: self[name], self.iterkeys())

    def __iter__(self):
        return self.iterkeys()

    def __getitem__(self, name):
        return getattr(self, name)

    def get(self, name, default = None):
        try:
            return self[name]
        except AttributeError:
            if default is not None:
                return default
            raise AttributeError

    

elixir.setup_all(bind=None)

def createInitialData(session):
    for country in (u'SE', u'NO', u'FI', u'DK'):
        for provider  in (u'Comm2', u'BandCorp', u'Fieacomm', u'OFelia'):
            for technology in (u'modem', u'DSL1', u'DSL2', u'cable'):
                for price in (u'100-200', u'200-300', u'300-400', u'400-'):
                    session.save(Service(country = country, provider = provider, technology = technology, price = price))
