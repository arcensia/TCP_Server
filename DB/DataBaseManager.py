from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import logging
from DB.DB_info import db_info


class DatabaseManager(db_info):
    def __init__(self, db_config):
        super().__init__()
        self.connection = None
        self.session = None
        self.url = None
        self.db_type = None
        self.engine = None
        self.Session = None
        self.config = db_config
        self.set_url()

    def set_url(self):
        db_info = self.config
        try:
            # DB 연결설정
            host = db_info['ip']
            database = db_info['name']
            username = self.username
            password = self.password
            self.db_type = db_info['type']
            encoded_password = quote_plus(password)
            self.url = f"{username}:{encoded_password}@{host}/{database}"

        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def init_engine(self):
        try:
            if self.db_type == 'mysql':
                self.engine = create_engine(
                    f"mysql+pymysql://{self.url}")

            elif self.db_type == 'mssql':
                import pyodbc  # pyinstaller 사용시 필요
                self.engine = create_engine(
                    f"mssql+pyodbc://{self.url}?driver=ODBC+Driver+17+for+SQL+Server")
            else:
                raise ValueError("Unsupported database type.")
        except Exception as e:
            raise ValueError(f"Failed to initialize engine: {e}")
        return True

    def open_session(self):
        try:
            if self.Session is None:
                self.init_engine()
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

            logging.info("Open DB Session")
            # print("Open ORM Session")
        except Exception as e:
            logging.warning(e)
            print(e)
            return False
        return True

    def close_session(self):
        self.session.close_all()

    def open_connection(self):
        try:
            if self.engine is None:
                self.init_engine()
            self.engine.connect()
            return True
        except Exception as e:
            return False
