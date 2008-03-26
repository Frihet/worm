import elixir, itertools
import Worm, Worm.Utils, Worm.Demo.Table.Config

__session__ = None

engine = Worm.Utils.create_engine(Worm.Demo.Table.Config.database_url)

class Service(Worm.Table.Model.DBModel, elixir.entity.Entity):
    country = elixir.Field(elixir.Unicode)
    provider = elixir.Field(elixir.Unicode)
    technology = elixir.Field(elixir.Unicode)
    price = elixir.Field(elixir.Unicode)

elixir.setup_all(bind=None)

def createInitialData(session):
    for country in (u'SE', u'NO', u'FI', u'DK'):
        for provider  in (u'Comm2', u'BandCorp', u'Fieacomm', u'OFelia'):
            for technology in (u'modem', u'DSL1', u'DSL2', u'cable'):
                for price in (u'100-200', u'200-300', u'300-400', u'400-'):
                    session.save(Service(country = country, provider = provider, technology = technology, price = price))
