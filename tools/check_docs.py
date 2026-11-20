"""Check local Markdown links without network access or third-party dependencies."""
from pathlib import Path
import re
from urllib.parse import unquote,urlsplit

def check(root):
    failures=[]
    for path in [root/'README.md',*sorted((root/'docs').glob('*.md'))]:
        text=path.read_text(encoding='utf-8')
        for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)',text):
            target=target.strip('<>')
            if urlsplit(target).scheme or target.startswith('#'):continue
            relative=unquote(target.split('#',1)[0])
            if relative and not (path.parent/relative).exists():failures.append(f'{path.relative_to(root)}: {target}')
    if failures:raise ValueError('Broken documentation links:\n'+'\n'.join(failures))
    print('Local README/documentation links verified.')

if __name__=='__main__':check(Path(__file__).resolve().parents[1])
