from flask import Flask, render_template

app=Flask(__name__)

import config
config.init_app(app)
import models
models.init_db(app)
from controllers import main
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)