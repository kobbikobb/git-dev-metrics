from git_dev_metrics.github import load_last_org, save_last_org


class TestOrgCache:
    def test_should_save_org_to_keyring(self, mocker):
        mock_set_password = mocker.patch("keyring.set_password")

        save_last_org("myorg")

        mock_set_password.assert_called_once_with("github-dev-metrics", "last_org", "myorg")

    def test_should_load_saved_org(self, mocker):
        mocker.patch("keyring.get_password", return_value="myorg")

        result = load_last_org()

        assert result == "myorg"

    def test_should_return_none_when_no_saved_org(self, mocker):
        mocker.patch("keyring.get_password", return_value=None)

        result = load_last_org()

        assert result is None

    def test_should_return_none_on_keyring_error(self, mocker):
        mocker.patch("keyring.get_password", side_effect=Exception("keyring error"))

        result = load_last_org()

        assert result is None
