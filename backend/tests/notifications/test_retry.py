from app.notifications.retry import RetryPolicy


def test_retry_policy_defaults():
    policy = RetryPolicy()

    assert policy.max_retries == 3
    assert policy.base_delay_seconds == 2
    assert policy.max_delay_seconds == 60


def test_calculate_delay():
    policy = RetryPolicy()

    assert policy.calculate_delay(0) == 0
    assert policy.calculate_delay(1) == 2
    assert policy.calculate_delay(2) == 4
    assert policy.calculate_delay(3) == 8


def test_delay_is_capped():
    policy = RetryPolicy(
        base_delay_seconds=10,
        max_delay_seconds=30,
    )

    assert policy.calculate_delay(1) == 10
    assert policy.calculate_delay(2) == 20
    assert policy.calculate_delay(3) == 30
    assert policy.calculate_delay(10) == 30


def test_can_retry():
    policy = RetryPolicy(max_retries=3)

    assert policy.can_retry(0) is True
    assert policy.can_retry(1) is True
    assert policy.can_retry(2) is True
    assert policy.can_retry(3) is False
    assert policy.can_retry(4) is False