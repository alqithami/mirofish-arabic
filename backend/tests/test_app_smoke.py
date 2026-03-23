import sys
from pathlib import Path
import unittest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class AppSmokeTest(unittest.TestCase):
    def test_health_endpoint(self):
        for name in [
            'flask', 'app', 'app.services', 'app.utils', 'app.utils.locale', 'app.services.zep_tools', 'app.services.report_ui'
        ]:
            sys.modules.pop(name, None)
        from app import create_app

        app = create_app()
        client = app.test_client()
        response = client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['status'], 'ok')
        self.assertIn('MiroFish Backend', payload['service'])


if __name__ == '__main__':
    unittest.main()
