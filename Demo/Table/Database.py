import sqlalchemy, sqlalchemy.orm
import Worm.Demo.Table.Config

def create_engine():
    engine = sqlalchemy.create_engine(Worm.Demo.Table.Config.database_url)
    engine.session_arguments = {'autoflush': False,
                                'transactional': True}
    def sessions(**kws):
        real_kws = {}
        real_kws.update(engine.session_arguments)
        real_kws.update(kws)
        class Session(sqlalchemy.orm.sessionmaker(bind=engine, **real_kws)):
            def __enter__(self):
                return self

            def __exit__(self, type, value, traceback):
                if type is None and value is None and traceback is None:
                    self.flush()
                    self.commit()
                else:
                    self.rollback()
                self.close()
        return Session
    engine.sessions = sessions
    engine.Session = sessions()
    return engine

engine = create_engine()
