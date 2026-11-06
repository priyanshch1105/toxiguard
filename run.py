from backend.app import app
from backend.config import Config

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=False)
