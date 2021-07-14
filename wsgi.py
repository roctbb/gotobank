from init import create_app, db
from config import *
from flask_migrate import Migrate


app = create_app()
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(port=PORT, host=HOST, debug=(not PRODUCTION))
