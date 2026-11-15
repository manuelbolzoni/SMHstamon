"""Run with: python -m unittest discover -s tests -p test_smhub.py -v."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['PYTHON_KEYRING_BACKEND'] = 'keyring.backends.null.Keyring'
import sys
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

# Config is initialized on import; never touch the user's real configuration.
_config = tempfile.TemporaryDirectory()
_argv = sys.argv[:]
sys.argv = [sys.argv[0], _config.name]
from Nagstamon.Config import conf, Server
from Nagstamon.Servers import create_server, SERVER_TYPES
from Nagstamon.Servers.SMHub import SMHubServer
import requests
sys.argv = _argv

PAYLOAD = {'summary': {'label': 'shared label'}, 'agents': {
    '1': {'name': 'SAP', 'component': 'ABAP', 'status': 'critical',
          'notes': 'test alarm', 'lastcheck': '12:00:00 01/11/2026',
          'lastok': '11:00:00 01/11/2026'}}}


def make_server(name):
    config = Server()
    config.name = name
    config.type = 'SMHUB'
    config.enabled = True
    config.monitor_url = 'https://example.invalid/' + name
    conf.servers[name] = config
    server = create_server(config)
    server.init_HTTP()
    return server


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server('first')
        self.response = Mock(status_code=200)
        self.response.json.return_value = deepcopy(PAYLOAD)
        self.server.session.get = Mock(return_value=self.response)

    def tearDown(self):
        self.server.session.close()
        conf.servers.clear()

    def test_only_smhub_is_registered(self):
        self.assertEqual(list(SERVER_TYPES), ['SMHUB'])

    def test_two_servers_same_labels_keep_independent_alarms(self):
        second = make_server('second')
        try:
            second.session.get = Mock(return_value=self.response)
            self.assertEqual(self.server.GetStatus().error, '')
            self.assertEqual(second.GetStatus().error, '')
            self.assertEqual(self.server.critical, 1)
            self.assertEqual(second.critical, 1)
            host = self.server.hosts['SHARED LABEL']
            self.assertEqual((host.name, host.server, host.status),
                             ('SHARED LABEL', 'first', 'UP'))
            self.assertNotEqual(self.server.events_current, second.events_current)
            self.response.json.return_value = {'summary': {'label': 'shared label'}, 'agents': {}}
            second.GetStatus()
            self.assertEqual(second.critical, 0)
            self.assertEqual(self.server.critical, 1)
        finally:
            second.session.close()

    def test_request_uses_configured_timeout_and_reuses_session(self):
        session = self.server.session
        self.server.init_HTTP()
        self.assertIs(self.server.session, session)
        self.server._get_status()
        session.get.assert_called_once_with(url=self.server.monitor_url, timeout=self.server.timeout)

    def test_http_failure_is_not_an_all_clear(self):
        self.server.GetStatus()
        self.response.status_code = 503
        self.response.raise_for_status.side_effect = requests.HTTPError('503 unavailable')
        result = self.server.GetStatus()
        self.assertTrue(result.error)
        self.assertEqual(self.server.critical, 1)

    def test_timeout_and_bad_json_are_reported(self):
        for error in (requests.Timeout('timed out'), ValueError('invalid JSON')):
            with self.subTest(error=error):
                self.server.session.get.side_effect = error
                self.assertTrue(self.server._get_status().error)

    def test_unknown_spelling_and_null_notes(self):
        self.response.json.return_value['agents']['1'].update(status='unknown', notes=None)
        self.assertEqual(self.server.GetStatus().error, '')
        self.assertEqual(self.server.unknown, 1)

    def test_tls_configuration_and_no_authentication(self):
        self.server.session.close()
        self.server.session = None
        self.server.ignore_cert = False
        self.server.custom_cert_use = True
        self.server.custom_cert_ca_file = 'company-ca.pem'
        self.server.init_HTTP()
        self.assertEqual(self.server.session.verify, 'company-ca.pem')
        self.assertFalse(self.server.session.trust_env)
        prepared = requests.Request('GET', 'https://example.invalid').prepare()
        self.assertNotIn('Authorization', self.server.session.auth(prepared).headers)


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conf.servers.clear()
        import Nagstamon.QUI as gui
        cls.gui = gui

    @classmethod
    def tearDownClass(cls):
        gui = cls.gui
        gui.statuswindow.worker.running = False
        gui.statuswindow.worker_notification.running = False
        for thread in gui.statuswindow.findChildren(gui.QThread):
            thread.quit()
            thread.wait(5000)
        gui.statuswindow.hide()

    def test_settings_pages_and_shortcuts(self):
        settings = self.gui.dialogs.settings
        settings.initialize()
        tabs = settings.window.tabs
        self.assertEqual([tabs.widget(i).objectName() for i in range(tabs.count())],
                         ['tab_servers', 'tab_display', 'tab_notifications', 'tab_colors'])
        with patch.object(settings.window, 'exec', return_value=0):
            settings.show(tab=4)
            self.assertIs(tabs.currentWidget(), settings.window.tab_notifications)
            settings.show(tab=2)
            self.assertIs(tabs.currentWidget(), settings.window.tab_servers)
        self.assertTrue(self.gui.statuswindow.toparea.button_filters.isHidden())

    def test_add_two_servers_hide_healthy_and_delete(self):
        gui = self.gui
        response = Mock(status_code=200)
        response.json.return_value = deepcopy(PAYLOAD)
        with patch('requests.Session.get', return_value=response):
            for name in ('server A', 'server B'):
                with patch.object(gui.dialogs.server.window, 'exec', return_value=0):
                    gui.dialogs.server.new()
                gui.dialogs.server.window.input_lineedit_name.setText(name)
                gui.dialogs.server.window.input_lineedit_monitor_url.setText('https://example.invalid/api')
                gui.dialogs.server.ok()
            boxes = [box for box in gui.statuswindow.servers_vbox.children()
                     if hasattr(box, 'server')]
            self.assertEqual([box.server.name for box in boxes], ['server A', 'server B'])
            for box in boxes:
                box.table.worker_thread.quit()
                self.assertTrue(box.table.worker_thread.wait(5000))
            # Mixed health: a healthy server is hidden while the other shows alarms.
            boxes[0].show_all()
            boxes[1].hide_all()
            self.assertTrue(boxes[0].table.is_shown)
            self.assertFalse(boxes[1].table.is_shown)
            for box in boxes:
                box.delete()


if __name__ == '__main__':
    unittest.main()
