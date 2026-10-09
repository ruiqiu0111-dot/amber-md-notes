from pathlib import Path
from html.parser import HTMLParser
import ast, re, html
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.ids=[]; self.links=[]; self.stack=[]; self.errors=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d: self.ids.append(d['id'])
        if tag=='a' and d.get('href','').startswith('#'): self.links.append(d['href'][1:])
        if tag in {'div','pre','table','section','aside','nav'}: self.stack.append(tag)
    def handle_endtag(self,tag):
        if tag in {'div','pre','table','section','aside','nav'}:
            if not self.stack or self.stack[-1]!=tag: self.errors.append((tag,self.stack[-3:]))
            else: self.stack.pop()
p=Page(); source=Path('index.html').read_text(encoding='utf-8'); p.feed(source)
print('Duplicate IDs:', sorted({x for x in p.ids if p.ids.count(x)>1}))
print('Broken anchors:', sorted(set(p.links)-set(p.ids)))
print('Structural nesting:',p.errors,'open:',p.stack)
failures=[]; total=0
for m in re.finditer(r'<span class="lang">([^<]*Python[^<]*)</span>.*?<pre>(.*?)</pre>',source,re.S):
    label=m.group(1); code=html.unescape(m.group(2)); total+=1
    try: ast.parse(code)
    except SyntaxError as e: failures.append((label,e.lineno,e.msg))
print('Python snippets parsed:',total,'syntax failures:',failures)
assert not p.errors and not p.stack
assert not set(p.links)-set(p.ids)
