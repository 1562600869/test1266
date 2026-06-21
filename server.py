import http.server
import json
import os
import urllib.parse

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')


class Handler(http.server.BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_static(self, path, content_type):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.send_static(os.path.join(TEMPLATES_DIR, 'index.html'), 'text/html; charset=utf-8')
            return

        if path.startswith('/static/'):
            filename = path[len('/static/'):]
            filepath = os.path.join(STATIC_DIR, filename)
            if not os.path.commonpath([STATIC_DIR, filepath]) == STATIC_DIR:
                self.send_response(403)
                self.end_headers()
                return
            if filepath.endswith('.css'):
                self.send_static(filepath, 'text/css; charset=utf-8')
            elif filepath.endswith('.js'):
                self.send_static(filepath, 'application/javascript; charset=utf-8')
            else:
                self.send_static(filepath, 'application/octet-stream')
            return

        if path == '/api/players':
            self.send_json(database.list_players())
            return

        if path == '/api/camps':
            self.send_json(database.list_camps())
            return

        if path == '/api/registrations':
            self.send_json(database.list_registrations())
            return

        if path == '/api/checkins':
            self.send_json(database.list_checkins())
            return

        if path.startswith('/api/player/') and path.endswith('/checkins/month'):
            try:
                player_id = int(path.split('/')[3])
                self.send_json(database.get_player_monthly_checkins(player_id))
            except (ValueError, IndexError):
                self.send_json({'error': '无效的球员ID'}, 400)
            return

        if path == '/api/stats/registrations/monthly':
            self.send_json(database.get_monthly_registration_by_age_group())
            return

        if path == '/api/config':
            self.send_json({
                'age_groups': database.AGE_GROUPS,
                'positions': database.POSITIONS,
                'camp_statuses': database.CAMP_STATUSES
            })
            return

        self.send_json({'error': 'Not Found'}, 404)

    def read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(content_length)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = json.loads(self.read_body().decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json({'error': '无效的JSON'}, 400)
            return

        if path == '/api/players':
            try:
                pid = database.add_player(
                    body['nickname'], body['phone'],
                    body['age_group'], body['position']
                )
                self.send_json({'success': True, 'id': pid})
            except KeyError as e:
                self.send_json({'error': f'缺少字段: {e}'}, 400)
            except Exception as e:
                self.send_json({'error': str(e)}, 400)
            return

        if path == '/api/camps':
            try:
                cid = database.add_camp(
                    body['name'], body['start_date'], body['end_date'],
                    int(body['fee']), int(body['max_capacity']),
                    body.get('status', '报名中')
                )
                self.send_json({'success': True, 'id': cid})
            except KeyError as e:
                self.send_json({'error': f'缺少字段: {e}'}, 400)
            except Exception as e:
                self.send_json({'error': str(e)}, 400)
            return

        if path == '/api/register':
            try:
                result = database.register_player(int(body['player_id']), int(body['camp_id']))
                self.send_json(result)
            except KeyError as e:
                self.send_json({'error': f'缺少字段: {e}'}, 400)
            except Exception as e:
                self.send_json({'success': False, 'message': str(e)})
            return

        if path == '/api/checkin':
            try:
                result = database.checkin_player(int(body['player_id']), int(body['camp_id']))
                self.send_json(result)
            except KeyError as e:
                self.send_json({'error': f'缺少字段: {e}'}, 400)
            except Exception as e:
                self.send_json({'success': False, 'message': str(e)})
            return

        self.send_json({'error': 'Not Found'}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = json.loads(self.read_body().decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json({'error': '无效的JSON'}, 400)
            return

        if path.startswith('/api/players/'):
            try:
                player_id = int(path.split('/')[-1])
                database.update_player(
                    player_id, body['nickname'], body['phone'],
                    body['age_group'], body['position']
                )
                self.send_json({'success': True})
            except (ValueError, IndexError):
                self.send_json({'error': '无效的球员ID'}, 400)
            except KeyError as e:
                self.send_json({'error': f'缺少字段: {e}'}, 400)
            except Exception as e:
                self.send_json({'error': str(e)}, 400)
            return

        if path.startswith('/api/camps/'):
            try:
                camp_id = int(path.split('/')[-1])
                database.update_camp(
                    camp_id, body['name'], body['start_date'], body['end_date'],
                    int(body['fee']), int(body['max_capacity']), body['status']
                )
                self.send_json({'success': True})
            except (ValueError, IndexError):
                self.send_json({'error': '无效的营期ID'}, 400)
            except KeyError as e:
                self.send_json({'error': f'缺少字段: {e}'}, 400)
            except Exception as e:
                self.send_json({'error': str(e)}, 400)
            return

        self.send_json({'error': 'Not Found'}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/players/'):
            try:
                player_id = int(path.split('/')[-1])
                database.delete_player(player_id)
                self.send_json({'success': True})
            except (ValueError, IndexError):
                self.send_json({'error': '无效的球员ID'}, 400)
            except Exception as e:
                self.send_json({'error': str(e)}, 400)
            return

        if path.startswith('/api/camps/'):
            try:
                camp_id = int(path.split('/')[-1])
                database.delete_camp(camp_id)
                self.send_json({'success': True})
            except (ValueError, IndexError):
                self.send_json({'error': '无效的营期ID'}, 400)
            except Exception as e:
                self.send_json({'error': str(e)}, 400)
            return

        self.send_json({'error': 'Not Found'}, 404)

    def log_message(self, format, *args):
        pass


def main():
    database.init_db()
    port = 6294
    server = http.server.HTTPServer(('localhost', port), Handler)
    print(f'服务器启动在 http://localhost:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')
        server.shutdown()


if __name__ == '__main__':
    main()
