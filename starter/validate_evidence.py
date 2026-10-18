"""Check captured acceptance evidence; never create or substitute model outputs."""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parent/'evidence'
checks={'01-order':['ORD-001','TRK987654321','UPS'],'02-refund':['approved','REF-','3-5'],'03-rag':['same-day','15%','priority'],'04-memory-a':['Jane','concise'],'04-memory-b':['Jane','concise'],'05-discount':['agentcore_code_interpreter','"tier_discount_pct": 10','"tier_discount": "11.00"','"final_total": "99.00"','"remaining_points": 349'],'06-browser':['Learn the Latest Tech Skills','https://www.udacity.com/']}
for name,expected in checks.items():
 r=json.loads((root/(name+'.json')).read_text(encoding='utf-8'))
 assert r['exit_code']==0, name+' CLI error'
 output=' '.join(r['stdout'].split()).lower()
 assert all(x.lower() in output for x in expected), name+' missing expected result'
 assert 'traceback (most recent call last)' not in output and '"error_type"' not in output, name+' runtime exception'
 if name=='06-browser':assert not any(x in output for x in ['unable to access','not available in this environment','cannot access'])
 print('PASS:',name)
print('All six scenarios (seven invocations including memory) have matching captured evidence.')
