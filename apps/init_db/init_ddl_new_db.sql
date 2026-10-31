-- Расширение для UUID (если ещё не включено)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

drop table if EXISTS command_log cascade;
DROP TABLE IF EXISTS user_house_room CASCADE;
DROP TABLE IF EXISTS telemetry_reading CASCADE;
DROP TABLE IF EXISTS device_state     CASCADE;
DROP TABLE IF EXISTS device           CASCADE;
DROP TABLE IF EXISTS room             CASCADE;
DROP TABLE IF EXISTS house            CASCADE;
DROP TABLE IF EXISTS user_account     CASCADE;


-- ============================================================
-- 1. account — пользователи (житель, оператор, администратор)
-- ============================================================
CREATE TABLE user_account (
    id            BIGSERIAL    PRIMARY KEY,
    name          VARCHAR(100) NOT NULL CHECK (length(trim(name)) > 0),
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT null,
    role VARCHAR(20) NOT NULL DEFAULT 'resident'
     CHECK (role IN ('resident', 'operator', 'admin')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_account_role ON user_account(role);

-- ============================================================
-- 2. home — дома (SaaS-тенанты)
-- ============================================================

CREATE TABLE house (
    id         BIGSERIAL PRIMARY key,
    name       VARCHAR(255) NOT NULL,
    address    VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

--CREATE INDEX idx_homes_owner ON homes(owner_id);

-- ============================================================
-- 3. room — комнаты/зоны внутри дома
-- ============================================================


CREATE TABLE room (
    id      BIGSERIAL PRIMARY key,
    house_id BIGINT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    name    VARCHAR(255) NOT null,
    UNIQUE (house_id, name)
);

CREATE INDEX IF NOT EXISTS idx_room_house_id ON room(house_id);

-- ============================================================
-- 4. user_house_room — привязка пользователя к локации
-- ============================================================

CREATE TABLE user_house_room (
    id            BIGSERIAL PRIMARY key,
    user_account_id       BIGINT NOT NULL REFERENCES user_account(id) on delete cascade,
    house_id      BIGINT NOT NULL REFERENCES house(id) on delete cascade,
    room_id       BIGINT NULL REFERENCES room(id) on delete set null,
    is_active BOOLEAN NOT NULL DEFAULT true
    );


-- Уникальность: пользователь + дом + комната (для строк с комнатой)
CREATE UNIQUE INDEX IF NOT EXISTS uq_uhr_user_house_room
    ON user_house_room(user_account_id, house_id, room_id)
    WHERE room_id IS NOT NULL;

-- Уникальность: пользователь + дом (для строк без комнаты)
CREATE UNIQUE INDEX IF NOT EXISTS uq_uhr_user_house_no_room
    ON user_house_room(user_account_id, house_id)
    WHERE room_id IS NULL;


-- ============================================================
-- 5. devices — устройства (датчики, актуаторы, камеры - 'sensor', 'actuator', 'camera', 'gateway')
-- ============================================================  
   
 CREATE TABLE device (
    id               BIGSERIAL PRIMARY key,
    house_id         BIGINT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    room_id          BIGINT REFERENCES room(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL
     CHECK (type IN ('sensor', 'actuator', 'camera', 'gateway')),
    vendor           VARCHAR(100),
    model            VARCHAR(100),
    firmware_version VARCHAR(50),
    online           BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen_at     TIMESTAMPTZ,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_device_house_id ON device(house_id);
CREATE INDEX IF NOT EXISTS idx_device_room_id  ON device(room_id);
CREATE INDEX IF NOT EXISTS idx_device_online   ON device(online);  


-- ============================================================
-- 6. device_state — текущие показатели устройства (key-value)
-- ============================================================
CREATE TABLE device_state (
    id         BIGSERIAL PRIMARY key,
    device_id  BIGINT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
    property   VARCHAR(100) NOT NULL,   -- temperature | motion | power | lock
    value      VARCHAR(255) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (device_id, property)
);

CREATE INDEX idx_states_device ON device_state(device_id);



-- ============================================================
-- 7. telemetry_readings — сырые показания датчиков (append-only)
-- ============================================================

CREATE TABLE telemetry_reading (
    id          BIGSERIAL        PRIMARY KEY,
    device_id   BIGINT           NOT NULL REFERENCES device(id) ON DELETE CASCADE,
    metric      VARCHAR(100)     NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    unit        VARCHAR(20),
    recorded_at TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_readings_device_ts
    ON telemetry_reading(device_id, recorded_at DESC);


-- ============================================================
-- 10. command_log — журнал команд устройству
-- ============================================================
CREATE TABLE command_log (
    id         BIGSERIAL        PRIMARY KEY,
    device_id  BIGINT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
    command    VARCHAR(50) NOT NULL,
	status VARCHAR(20) NOT NULL DEFAULT 'pending'
       CHECK (status IN ('pending', 'sent', 'executed', 'failed', 'timeout')),
    reason     VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

CREATE INDEX idx_commands_device ON command_log(device_id, created_at DESC);
CREATE INDEX idx_commands_status ON command_log(status);
