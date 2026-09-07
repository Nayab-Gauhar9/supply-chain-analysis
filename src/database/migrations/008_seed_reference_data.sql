INSERT INTO countries (
    country_code,
    country_name,
    iso_code
)
VALUES
    (699, 'India', 'IN'),
    (251, 'France', 'FR'),
    (643, 'Russia', 'RU'),
    (826, 'United Kingdom', 'GB'),
    (156, 'China', 'CN')
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO commodities (
    commodity_code,
    commodity_name
)
VALUES
    ('2709', 'Crude petroleum'),
    ('2710', 'Refined petroleum'),
    ('2711', 'Natural gas'),
    ('2701', 'Coal'),
    ('2601', 'Iron ore'),
    ('7403', 'Copper'),
    ('7601', 'Aluminium'),
    ('8542', 'Integrated circuits'),
    ('1001', 'Wheat'),
    ('3004', 'Medicaments')
ON CONFLICT (commodity_code) DO NOTHING;

INSERT INTO transport_modes (
    mot_code,
    mot_name
)
VALUES
    (0,    'Total modes of transport'),
    (1000, 'Air'),
    (2100, 'Sea'),
    (3100, 'Railway'),
    (3200, 'Road'),
    (9000, 'Not elsewhere classified'),
    (9200, 'Postal consignments, mail or courier shipment'),
    (9900, 'Other')
ON CONFLICT (mot_code) DO NOTHING;