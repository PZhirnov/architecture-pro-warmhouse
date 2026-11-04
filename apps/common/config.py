from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/smarthome"
    nats_url: str = "nats://nats:4222"

    temperature_threshold: float = 25.0
    humidity_threshold: float = 70.0
    co2_threshold: float = 1000.0
    illuminance_threshold: float = 100.0
    battery_threshold: float = 20.0
    rule_cooldown_sec: float = 60.0

    device_url: str = "http://device:8087"
    telemetry_url: str = "http://telemetry:8082"
    automation_url: str = "http://automation:8083"
    location_url: str = "http://location:8085"
    user_url: str = "http://user:8086"

    mqtt_host: str = "mqtt"
    mqtt_port: int = 1883

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
