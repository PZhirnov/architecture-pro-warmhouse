-- Таблица монолита на GO
-- Create the sensors table
CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    value FLOAT DEFAULT 0,
    unit VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sensors_type ON sensors(type);
CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors(location);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);

-- Новое решение
--=====================================================

-- Пользователи
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- 1. user_account — пользователи платформы
CREATE TABLE IF NOT EXISTS user_account (
    id            BIGSERIAL    PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'resident'
                  CHECK (role IN ('resident', 'operator', 'admin')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- Локации для размещения датчиков (SaaS-тенанты)
CREATE TABLE IF NOT EXISTS house (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS room (
    id BIGSERIAL PRIMARY KEY,
    house_id BIGINT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    UNIQUE (house_id, name)
);

-- Связываем пользователя с локацией
CREATE TABLE IF NOT EXISTS user_house (
    id         BIGSERIAL   PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    house_id   BIGINT      NOT NULL REFERENCES house(id)        ON DELETE CASCADE,
    room_id    BIGINT      REFERENCES room(id) ON DELETE SET NULL,
    role       VARCHAR(20) NOT NULL DEFAULT 'resident'
               CHECK (role IN ('resident', 'operator', 'admin')),
    is_active  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Уникальность: пользователь + дом + комната (для записей с комнатой)
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_house_room
    ON user_house(user_id, house_id, room_id)
    WHERE room_id IS NOT NULL;

-- Уникальность: пользователь + дом (для записей без комнаты)
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_house_no_room
    ON user_house(user_id, house_id)
    WHERE room_id IS NULL;

-- =============================================
-- Таблицы для хранения данных сервисов:
-- =============================================

-- Управление устройствами
CREATE TABLE IF NOT EXISTS device (
    id BIGSERIAL PRIMARY KEY,
    house_id BIGINT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    room_id BIGINT REFERENCES room(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('sensor','actuator','camera','gateway')),
    vendor VARCHAR(100),
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    online BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- Телеметрия
CREATE TABLE IF NOT EXISTS telemetry_reading (
    id BIGSERIAL PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
    metric VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_readings_device_ts ON telemetry_reading(device_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS command_log (
    id BIGSERIAL PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
    command VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','sent','executed','failed','timeout')),
    reason VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

-- Автоматизация
-- automation_rule — правило целиком (условия + действия в JSONB)
-- ============================================================
CREATE TABLE IF NOT EXISTS automation_rule (
    id                BIGSERIAL    PRIMARY KEY,
    house_id          BIGINT       NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    enabled           BOOLEAN      NOT NULL DEFAULT TRUE,

    -- AND — все условия должны совпасть; OR — достаточно одного
    logic_operator    VARCHAR(3)   NOT NULL DEFAULT 'AND'
                      CHECK (logic_operator IN ('AND','OR')),

    -- [{"device_id":1,"metric":"temperature","operator":"gt","threshold":25.0}]
    conditions        JSONB        NOT NULL,

    -- [{"type":"device_command","target_device_id":3,"command":"switch_off"}]
    actions           JSONB        NOT NULL,

    priority          INT          NOT NULL DEFAULT 100,
    cooldown_seconds  INT          NOT NULL DEFAULT 60,
    last_triggered_at TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- базовая валидация JSONB: массивы непустые
    CONSTRAINT chk_rule_conditions_is_array
        CHECK (jsonb_typeof(conditions) = 'array'),
    CONSTRAINT chk_rule_conditions_not_empty
        CHECK (jsonb_array_length(conditions) > 0),
    CONSTRAINT chk_rule_actions_is_array
        CHECK (jsonb_typeof(actions) = 'array'),
    CONSTRAINT chk_rule_actions_not_empty
        CHECK (jsonb_array_length(actions) > 0)
);

CREATE INDEX IF NOT EXISTS idx_automation_rule_house_enabled
    ON automation_rule(house_id, enabled);

-- GIN-индекс: быстрый поиск правил, затрагивающих конкретный device_id
CREATE INDEX IF NOT EXISTS idx_automation_rule_conditions_gin
    ON automation_rule USING GIN (conditions jsonb_path_ops);

-- ============================================================
-- automation_execution_log — журнал срабатываний (аудит)
-- ============================================================
CREATE TABLE IF NOT EXISTS automation_execution_log (
    id                 BIGSERIAL   PRIMARY KEY,
    rule_id            BIGINT      NOT NULL REFERENCES automation_rule(id) ON DELETE CASCADE,
    status             VARCHAR(20) NOT NULL
                       CHECK (status IN ('success','failed','skipped')),
    reason             TEXT,

    -- снимок значений датчиков, приведших к срабатыванию
    condition_snapshot JSONB,

    -- что сделали (по каждому действию)
    action_result      JSONB,

    triggered_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_automation_execution_rule_ts
    ON automation_execution_log(rule_id, triggered_at DESC);


-- Демо-данные
-- Дома
INSERT INTO house (id, name, address) VALUES
  (1, 'Квартира на Ленина', 'г. Москва, ул. Ленина, д. 10, кв. 42'),
  (2, 'Загородный дом в Сосновке', 'МО, д. Сосновка, ул. Лесная, д. 5'),
  (3, 'Квартира на Невском', 'г. Санкт-Петербург, Невский пр., д. 100, кв. 15'),
  (4, 'Дача в Подмосковье', 'МО, СНТ Ромашка, уч. 23'),
  (5, 'Апартаменты в Сочи', 'г. Сочи, ул. Морская, д. 8, кв. 301'),
  (6, 'Студия в Казани', 'г. Казань, ул. Баумана, д. 12, кв. 7'),
  (7, 'Дом в Екатеринбурге', 'г. Екатеринбург, ул. Горького, д. 45'),
  (8, 'Квартира в Новосибирске', 'г. Новосибирск, ул. Красный проспект, д. 20, кв. 88'),
  (9, 'Таунхаус в Краснодаре', 'г. Краснодар, ул. Красная, д. 150, к. 2'),
  (10, 'Коттедж в Калининграде', 'г. Калининград, ул. Янтарная, д. 3')
ON CONFLICT DO NOTHING;

-- Комнаты
INSERT INTO room (id, house_id, name) VALUES
  -- Дом 1: 4 комнаты
  (1, 1, 'Гостиная'), (2, 1, 'Кухня'), (3, 1, 'Спальня'), (4, 1, 'Детская'),
  -- Дом 2: 4 комнаты
  (5, 2, 'Гостиная'), (6, 2, 'Кухня'), (7, 2, 'Спальня'), (8, 2, 'Терраса'),
  -- Дом 3: 3 комнаты
  (9, 3, 'Гостиная'), (10, 3, 'Кухня'), (11, 3, 'Спальня'),
  -- Дом 4: 3 комнаты
  (12, 4, 'Гостиная'), (13, 4, 'Кухня'), (14, 4, 'Веранда'),
  -- Дом 5: 3 комнаты
  (15, 5, 'Гостиная'), (16, 5, 'Спальня'), (17, 5, 'Балкон'),
  -- Дом 6: 1 комната
  (18, 6, 'Основная комната'),
  -- Дом 7: 4 комнаты
  (19, 7, 'Гостиная'), (20, 7, 'Кухня'), (21, 7, 'Спальня'), (22, 7, 'Кабинет'),
  -- Дом 8: 2 комнаты
  (23, 8, 'Гостиная'), (24, 8, 'Спальня'),
  -- Дом 9: 3 комнаты
  (25, 9, 'Гостиная'), (26, 9, 'Кухня'), (27, 9, 'Спальня'),
  -- Дом 10: 4 комнаты
  (28, 10, 'Гостиная'), (29, 10, 'Кухня'), (30, 10, 'Спальня'), (31, 10, 'Библиотека')
ON CONFLICT DO NOTHING;

-- Пользователи
INSERT INTO user_account (id, name, email, password_hash) VALUES
  (1, 'Иван Петров', 'admin@smarthome.local', crypt('password', gen_salt('bf'))),
  (2, 'Мария Сидорова', 'operator@smarthome.local', crypt('password', gen_salt('bf'))),
  (3, 'Алексей Кузнецов', 'resident@smarthome.local', crypt('password', gen_salt('bf'))),
  (4, 'Ольга Смирнова', 'olga.smirnova@example.com', crypt('password', gen_salt('bf'))),
  (5, 'Дмитрий Волков', 'dmitry.volkov@example.com', crypt('password', gen_salt('bf'))),
  (6, 'Екатерина Морозова', 'ekaterina.morozova@example.com', crypt('password', gen_salt('bf'))),
  (7, 'Сергей Новиков', 'sergey.novikov@example.com', crypt('password', gen_salt('bf'))),
  (8, 'Анна Фёдорова', 'anna.fedorova@example.com', crypt('password', gen_salt('bf'))),
  (9, 'Павел Козлов', 'pavel.kozlov@example.com', crypt('password', gen_salt('bf'))),
  (10, 'Татьяна Лебедева', 'tatiana.lebedeva@example.com', crypt('password', gen_salt('bf')))
ON CONFLICT DO NOTHING;

-- Привязки
INSERT INTO user_house (user_id, house_id, room_id, role) VALUES
  -- Иван - админ 3 домов
  (1, 1, NULL, 'admin'),
  (1, 2, NULL, 'admin'),
  (1, 7, NULL, 'admin'),
  -- Мария - оператор 3 домов
  (2, 1, NULL, 'operator'),
  (2, 2, NULL, 'operator'),
  (2, 3, NULL, 'operator'),
  -- Алексей - житель дома 1 (2 комнаты) и дома 2 (2 комнаты)
  (3, 1, 1, 'resident'), (3, 1, 2, 'resident'),
  (3, 2, 5, 'resident'), (3, 2, 6, 'resident'),
  -- Ольга - житель дома 3 (весь) и дома 4 (2 комнаты)
  (4, 3, NULL, 'resident'),
  (4, 4, 12, 'resident'), (4, 4, 13, 'resident'),
  -- Дмитрий - житель дома 5 (весь)
  (5, 5, NULL, 'resident'),
  -- Екатерина - житель дома 6 (весь) и дома 7 (гостиная)
  (6, 6, NULL, 'resident'),
  (6, 7, 19, 'resident'),
  -- Сергей - житель дома 8 и 9
  (7, 8, NULL, 'resident'),
  (7, 9, NULL, 'resident'),
  -- Анна - житель дома 10 (весь)
  (8, 10, NULL, 'resident'),
  -- Павел - оператор домов 7 и 10
  (9, 7, NULL, 'operator'),
  (9, 10, NULL, 'operator'),
  -- Татьяна - житель дома 1 (спальня)
  (10, 1, 3, 'resident')
ON CONFLICT DO NOTHING;

-- Устройства (реалистично по комнатам)
INSERT INTO device (id, house_id, room_id, type, vendor, model, firmware_version, online, last_seen_at) VALUES
  -- Дом 1 (Квартира на Ленина, 4 комнаты)
  (1,  1, 1, 'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '2 minutes'),
  (2,  1, 1, 'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '1 minute'),
  (3,  1, 2, 'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '5 minutes'),
  (4,  1, 2, 'actuator', 'Shelly',  'Relay 1',                             '2.0.9', TRUE, NOW() - INTERVAL '3 minutes'),
  (5,  1, 3, 'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '4 minutes'),
  (6,  1, 4, 'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '7 minutes'),
  (7,  1, NULL,'gateway','Zigbee',  'CC2531',                              '3.0.0', TRUE, NOW() - INTERVAL '1 minute'),
  -- Дом 2 (Загородный дом, 4 комнаты)
  (8,  2, 5, 'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '2 minutes'),
  (9,  2, 5, 'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '3 minutes'),
  (10, 2, 6, 'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '8 minutes'),
  (11, 2, 7, 'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '5 minutes'),
  (12, 2, 8, 'camera',   'TP-Link', 'Tapo C200',                           '1.1.5', TRUE, NOW() - INTERVAL '30 seconds'),
  (13, 2, NULL,'gateway','Zigbee',  'CC2531',                              '3.0.0', TRUE, NOW() - INTERVAL '2 minutes'),
  -- Дом 3 (Квартира на Невском, 3 комнаты)
  (14, 3, 9, 'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '1 minute'),
  (15, 3, 9, 'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '2 minutes'),
  (16, 3, 10,'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '6 minutes'),
  (17, 3, 11,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '3 minutes'),
  -- Дом 4 (Дача, 3 комнаты)
  (18, 4, 12,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '4 minutes'),
  (19, 4, 13,'actuator', 'Shelly',  'Relay 1',                             '2.0.9', TRUE, NOW() - INTERVAL '1 minute'),
  (20, 4, 14,'camera',   'TP-Link', 'Tapo C200',                           '1.1.5', FALSE,NOW() - INTERVAL '6 hours'),
  -- Дом 5 (Апартаменты в Сочи, 3 комнаты)
  (21, 5, 15,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '2 minutes'),
  (22, 5, 15,'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '3 minutes'),
  (23, 5, 16,'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '5 minutes'),
  (24, 5, 17,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', FALSE,NOW() - INTERVAL '2 days'),
  -- Дом 6 (Студия в Казани, 1 комната)
  (25, 6, 18,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '1 minute'),
  (26, 6, 18,'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '4 minutes'),
  -- Дом 7 (Дом в Екатеринбурге, 4 комнаты)
  (27, 7, 19,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '1 minute'),
  (28, 7, 19,'actuator', 'Shelly',  'Relay 1',                             '2.0.9', TRUE, NOW() - INTERVAL '2 minutes'),
  (29, 7, 20,'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '4 minutes'),
  (30, 7, 21,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '3 minutes'),
  (31, 7, 22,'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '2 minutes'),
  -- Дом 8 (Квартира в Новосибирске, 2 комнаты)
  (32, 8, 23,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '2 minutes'),
  (33, 8, 23,'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '3 minutes'),
  (34, 8, 24,'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '5 minutes'),
  -- Дом 9 (Таунхаус, 3 комнаты)
  (35, 9, 25,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '3 minutes'),
  (36, 9, 25,'actuator', 'Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '1 minute'),
  (37, 9, 26,'sensor',   'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '7 minutes'),
  (38, 9, 27,'sensor',   'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '2 minutes'),
  -- Дом 10 (Коттедж, 4 комнаты)
  (39, 10, 28,'sensor',  'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '1 minute'),
  (40, 10, 28,'actuator','Shelly',  'Plug S',                              '2.1.0', TRUE, NOW() - INTERVAL '3 minutes'),
  (41, 10, 29,'sensor',  'Aqara',   'Motion Sensor P1',                    '1.2.1', TRUE, NOW() - INTERVAL '5 minutes'),
  (42, 10, 30,'sensor',  'Xiaomi',  'Mi Temperature & Humidity Monitor 2', '1.0.3', TRUE, NOW() - INTERVAL '2 minutes'),
  (43, 10, 31,'camera',  'TP-Link', 'Tapo C200',                           '1.1.5', TRUE, NOW() - INTERVAL '45 seconds')
ON CONFLICT DO NOTHING;

-- ---------------- Правила автоматизации (5 штук на дома 1, 2, 3, 7, 10) ----------------
INSERT INTO automation_rule (id, house_id, name, description, logic_operator, enabled, priority, cooldown_seconds, conditions, actions) VALUES
    (1, 1,  'auto_off_on_hot', 'Если в гостиной или спальне жарко — выключить обогреватель',
        'OR', TRUE, 100, 60,
        '[{"device_id":1,"metric":"temperature","operator":"gt","threshold":25.0},
          {"device_id":5,"metric":"temperature","operator":"gt","threshold":25.0}]'::jsonb,
        '[{"type":"device_command","target_device_id":2,"command":"switch_off"}]'::jsonb),

    (2, 2,  'auto_off_on_hot', 'Если в гостиной или спальне жарко — выключить обогреватель',
        'OR', TRUE, 100, 60,
        '[{"device_id":8,"metric":"temperature","operator":"gt","threshold":25.0},
          {"device_id":11,"metric":"temperature","operator":"gt","threshold":25.0}]'::jsonb,
        '[{"type":"device_command","target_device_id":9,"command":"switch_off"}]'::jsonb),

    (3, 3,  'auto_off_on_hot', 'Если в гостиной или спальне жарко — выключить обогреватель',
        'OR', TRUE, 100, 60,
        '[{"device_id":14,"metric":"temperature","operator":"gt","threshold":26.0},
          {"device_id":17,"metric":"temperature","operator":"gt","threshold":26.0}]'::jsonb,
        '[{"type":"device_command","target_device_id":15,"command":"switch_off"}]'::jsonb),

    (4, 7,  'auto_off_on_hot', 'Если в гостиной или спальне жарко — выключить обогреватель',
        'OR', TRUE, 100, 60,
        '[{"device_id":27,"metric":"temperature","operator":"gt","threshold":25.0},
          {"device_id":30,"metric":"temperature","operator":"gt","threshold":25.0}]'::jsonb,
        '[{"type":"device_command","target_device_id":28,"command":"switch_off"}]'::jsonb),

    (5, 10, 'auto_off_on_hot', 'Если в гостиной или спальне жарко — выключить обогреватель',
        'OR', TRUE, 100, 60,
        '[{"device_id":39,"metric":"temperature","operator":"gt","threshold":25.0},
          {"device_id":42,"metric":"temperature","operator":"gt","threshold":25.0}]'::jsonb,
        '[{"type":"device_command","target_device_id":40,"command":"switch_off"}]'::jsonb)
    ON CONFLICT DO NOTHING;


SELECT setval(pg_get_serial_sequence('user_account', 'id'), (SELECT MAX(id) FROM user_account));
SELECT setval(pg_get_serial_sequence('house', 'id'), (SELECT MAX(id) FROM house));
SELECT setval(pg_get_serial_sequence('room', 'id'), (SELECT MAX(id) FROM room));
SELECT setval(pg_get_serial_sequence('user_house', 'id'), (SELECT MAX(id) FROM user_house));
SELECT setval(pg_get_serial_sequence('device', 'id'), (SELECT MAX(id) FROM device));
SELECT setval(pg_get_serial_sequence('automation_rule', 'id'),          GREATEST((SELECT MAX(id) FROM automation_rule), 1));
SELECT setval(pg_get_serial_sequence('automation_execution_log', 'id'), GREATEST((SELECT MAX(id) FROM automation_execution_log), 1));
