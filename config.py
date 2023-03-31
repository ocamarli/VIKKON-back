class Config:
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_DATABASE_URI = 'mongodb+srv://ocamar:xrfmX3Sr1YKv9S4k@vikkon.tdfkmfc.mongodb.net/demo?retryWrites=true&w=majority'
    MONGO_USERNAME = 'ocamar'
    MONGO_PASSWORD = 'xrfmX3Sr1YKv9S4k'
    API_JWT_SECRET = 'VIKKONAPISECRET001'

config = {
    'development': DevelopmentConfig,
}