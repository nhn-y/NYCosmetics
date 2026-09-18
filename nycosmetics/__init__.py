from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import cloudinary


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:admin%40123@localhost/nycosmeticsdb?charset=utf8mb4"
app.config["PAGE_SIZE"]=4
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
# app.config['CART_KEY'] = 'cart'
db = SQLAlchemy(app)

cloudinary.config(cloud_name='ddxrieh4l',
                  api_key='179483865123425',
                  api_secret='rWekQaukpy0Fxp9jDA3DMF1AMt8')

app.secret_key = "7f9c2e8a4b1d6f0c9e3a7b5d2f8c1e6a"

login = LoginManager(app)
login.login_view = "user_login"
login.login_message = "Vui lòng đăng nhập để sử dụng chức năng này!"
login.login_message_category = "warning"