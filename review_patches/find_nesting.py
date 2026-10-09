from pathlib import Path
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self): super().__init__(); self.stack=[]; self.errors=[]
    def handle_starttag(self,t,a):
        if t in {'div','pre','table','section','aside','nav'}: self.stack.append((t,self.getpos()[0],dict(a).get('id','')))
    def handle_endtag(self,t):
        if t in {'div','pre','table','section','aside','nav'}:
            if self.stack and self.stack[-1][0]==t: self.stack.pop()
            else: self.errors.append((t,self.getpos()))
for f in ['index.html','index.html.bak','WY/index.html']:
    p=P(); p.feed(Path(f).read_text(encoding='utf-8-sig')); print(f,p.stack,p.errors[:5])
