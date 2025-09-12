import json
import os
import sys
import time
import urllib.request


API = 'https://api.hetzner.cloud/v1'


def api(token: str, method: str, path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(API + path, method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            print(f"HTTP {e.code} {path}: {body}", file=sys.stderr)
        except Exception:
            print(f"HTTP {e.code} {path}", file=sys.stderr)
        raise


def main():
    token = os.environ.get('HCLOUD_TOKEN', '')
    if not token:
        print('HCLOUD_TOKEN is required', file=sys.stderr)
        sys.exit(2)

    pub_path = os.environ.get('SSH_PUB', 'deploy/codex_deploy_ed25519.pub')
    with open(pub_path, 'r') as f:
        pubkey = f.read().strip()

    # Create or find SSH key
    name = f'codex-deployer-{int(time.time())}'
    try:
        ssh = api(token, 'POST', '/ssh_keys', {'name': name, 'public_key': pubkey})
        ssh_id = ssh.get('ssh_key', {}).get('id')
    except Exception:
        ssh_id = None
    if not ssh_id:
        lst = api(token, 'GET', '/ssh_keys')
        ssh_id = next((k['id'] for k in lst.get('ssh_keys', []) if k.get('public_key') == pubkey), None)
        if not ssh_id:
            print('Failed to create/find SSH key', file=sys.stderr)
            sys.exit(3)

    # Create server (cx11)
    sv_name = f'fardayab-{int(time.time())}'
    server = api(token, 'POST', '/servers', {
        'name': sv_name,
        'server_type': 'cx22',
        'image': 'ubuntu-24.04',
        # Let Hetzner pick location automatically for availability
        'ssh_keys': [ssh_id],
        'automount': False,
    })
    sv = server.get('server', {})
    if not sv:
        print('Failed to create server', file=sys.stderr)
        sys.exit(4)
    out = {
        'server_id': sv.get('id'),
        'name': sv_name,
        'ipv4': (sv.get('public_net', {})
                 .get('ipv4') or {}).get('ip'),
        'ipv6': (sv.get('public_net', {})
                 .get('ipv6') or {}).get('ip'),
    }
    os.makedirs('deploy', exist_ok=True)
    with open('deploy/server_info.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
