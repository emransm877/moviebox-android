"""Check documented published assets separately from unreleased source versions."""
import argparse
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

def validate(root, online=False):
    config=json.loads((root/'release.json').read_text(encoding='utf-8'))
    repo=config['repository'];published=config['published_version'];source=config['source_version']
    for version in (published,source):
        if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid release version')
    if not re.fullmatch(r'emransm877/moviebox-(desktop|android)',repo):raise ValueError('Unexpected repository')
    if (root/'project.json').exists():
        actual=json.loads((root/'project.json').read_text(encoding='utf-8'))['patch_version']
    else:
        actual=re.search(r"APP_VERSION = '([^']+)'",(root/'main.py').read_text(encoding='utf-8')).group(1)
    if actual!=source:raise ValueError('Source version does not match release.json')
    readme=(root/'README.md').read_text(encoding='utf-8')
    for asset in config['assets']:
        expected=f'https://github.com/{repo}/releases/download/v{published}/{asset}'
        if expected not in readme:raise ValueError('README missing the published download: '+asset)
    pattern=r'https://github\.com/'+re.escape(repo)+r'/releases/(?:latest/download|download/[^/\s)]+)/([^\s)]+)'
    for asset in re.findall(pattern,readme):
        if asset not in config['assets'] and not asset.endswith('.sha256'):
            raise ValueError('README advertises an undeclared application asset: '+asset)
    if online:
        request=Request(f'https://api.github.com/repos/{repo}/releases/tags/v{published}',headers={'User-Agent':'MovieBox-release-review','Accept':'application/vnd.github+json'})
        with urlopen(request,timeout=20) as response:release=json.load(response)
        if release['draft'] or release['prerelease']:raise ValueError('Published download must be a stable, public release')
        assets={a['name']:a for a in release['assets']}
        for name in config['assets']:
            asset=assets.get(name)
            if not asset or asset['state']!='uploaded' or asset['size']<=0:raise ValueError('Missing or incomplete release asset: '+name)
            if name+'.sha256' not in assets and 'SHA256SUMS.txt' not in assets:raise ValueError('Missing checksum for '+name)
    print(f'{repo}: published {published}; source {source}; documented assets verified'+(' against GitHub' if online else ' offline'))
    return config

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--online',action='store_true');args=parser.parse_args()
    validate(Path(__file__).resolve().parents[1],args.online)
