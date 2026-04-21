import time
from app.config import settings


class OctoclickClient:
    def fetch_table(self, task):
        time.sleep(settings.request_delay_ms / 1000)
        # v1 placeholder until exact payload/headers are captured from Network.
        return {
            'meta': {'role': settings.octoclick_role, 'status': True, 'code': 200},
            'data': [
                {
                    'metric': {'Click': '46755', 'Ctr': '100', 'cpmWM': '1.1003', 'cpmN': '0.4693'},
                    'group': {
                        'Country': {'id': 2017370, 'name': 'Russia', 'field_name': 'Country'}
                    }
                }
            ]
        }


octoclick_client = OctoclickClient()
