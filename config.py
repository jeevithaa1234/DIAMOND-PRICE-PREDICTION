import os

class Config:
    SECRET_KEY = "diamond_prediction_secret_key"

    DATABASE = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "diamond.db"
    )