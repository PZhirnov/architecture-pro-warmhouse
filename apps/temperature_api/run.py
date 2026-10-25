from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=False)

"""
Проверка:
curl "http://localhost:8081/temperature?location=Bedroom"
curl "http://localhost:8081/temperature/3"
"""
