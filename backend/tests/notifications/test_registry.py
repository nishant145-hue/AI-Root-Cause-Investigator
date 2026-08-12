from app.notifications.registry import create_notification_manager


def test_notification_manager_registers_all_providers():
    manager = create_notification_manager()

    assert manager.get_provider("email").name == "email"
    assert manager.get_provider("slack").name == "slack"
    assert manager.get_provider("teams").name == "teams"