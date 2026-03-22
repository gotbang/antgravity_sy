from services.activity_radius_policy import build_safe_activity_radius


def test_safe_activity_radius_stays_within_supported_bounds():
    result = build_safe_activity_radius(
        {
            'market': 'US',
            'change_pct': 12.5,
            'volume': 10,
        },
        {'fearGreedIndex': 92},
    )

    assert 1.5 <= result['safe_activity_radius_pct'] <= 6.0
    assert result['safe_activity_level'] == 'danger'


def test_safe_activity_radius_expands_for_stable_market_conditions():
    result = build_safe_activity_radius(
        {
            'market': 'US',
            'change_pct': 0.4,
            'volume': 1_000_000,
        },
        {'fearGreedIndex': 50},
    )

    assert result['safe_activity_radius_pct'] == 5.5
    assert result['safe_activity_level'] == 'safe'


def test_safe_activity_labels_change_with_risk_context():
    safe_result = build_safe_activity_radius(
        {'market': 'US', 'change_pct': 0.2, 'volume': 900_000},
        {'fearGreedIndex': 48},
    )
    danger_result = build_safe_activity_radius(
        {'market': 'US', 'change_pct': 8.1, 'volume': 100},
        {'fearGreedIndex': 78},
    )

    assert safe_result['safe_activity_label'] != danger_result['safe_activity_label']
    assert '천천히' in safe_result['safe_activity_label']
    assert '피하는' in danger_result['safe_activity_label']
