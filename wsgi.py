from init import create_app, db
from config import *
from flask_script import Manager
from flask_migrate import Migrate


app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)

if __name__ == "__main__":
    app.run(port=PORT, host=HOST)
