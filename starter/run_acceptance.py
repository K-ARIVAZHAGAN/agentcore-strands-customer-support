"""Capture real Starter Toolkit CLI output for all six required scenarios."""
import argparse,json,os,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CASES=[('01-order',{'prompt':'Can you track order ORD-001?','customer_id':'CUST-123','session_id':'t1'}),('02-refund',{'prompt':'I want to return my Kindle Paperwhite (ORD-002). Please initiate a refund.','customer_id':'CUST-123','session_id':'t2'}),('03-rag',{'prompt':'What are the benefits of the Platinum loyalty tier?','customer_id':'CUST-123','session_id':'t3'}),('04-memory-a',{'prompt':'Hi, I am Jane. I prefer concise responses.','customer_id':'CUST-123','session_id':'s-A'}),('04-memory-b',{'prompt':'Do you remember my name and communication preference?','customer_id':'CUST-123','session_id':'s-B'}),('05-discount',{'prompt':'I am a Gold member with 4250 points. Calculate my discount on a $150 standard order.','customer_id':'CUST-123','session_id':'t5'}),('06-browser',{'prompt':'Go to https://www.udacity.com and tell me the page title. Use browser init_session with session_name udacity-session, then navigate, then evaluate document.title and location.href. If navigate times out waiting for network idle, still evaluate the title from the loaded page in that same session. Report only the actual evaluated title and URL.','customer_id':'CUST-456','session_id':'t6'})]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--case',choices=[c[0] for c in CASES]);args=parser.parse_args()
 env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',AGENTCORE_SUPPRESS_RECOMMENDATION='1')
 cli=ROOT/'.venv/Scripts/agentcore.exe' if os.name=='nt' else ROOT/'.venv/bin/agentcore'
 out=ROOT/'evidence';out.mkdir(exist_ok=True)
 for name,payload in CASES:
  if args.case and args.case!=name:continue
  if name=='04-memory-b' and not args.case:
   print('Waiting for long-term name/preference extraction...',flush=True)
   import main as implementation
   for attempt in range(8):
    texts=[]
    for template in implementation.get_namespaces(implementation.memory_client,implementation.MEMORY_ID).values():
     matches=implementation.memory_client.retrieve_memories(memory_id=implementation.MEMORY_ID,namespace=template.format(actorId='CUST-123'),query='customer name communication preference concise',top_k=5)
     texts.extend(r.get('content',{}).get('text','') for r in matches)
    found=' '.join(texts).lower()
    if 'jane' in found and 'concise' in found:break
    time.sleep(15)
   else:raise RuntimeError('Name/preference extraction not ready; rerun memory recall later.')
  command=[str(cli),'invoke',json.dumps(payload),'--session-id',str(uuid.uuid4())]
  print('Running',name,flush=True)
  run=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=420)
  record={'command':['agentcore',*command[1:]],'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
  (out/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
  (out/(name+'.txt')).write_text('COMMAND: '+json.dumps(record['command'])+'\nEXIT CODE: '+str(run.returncode)+'\n\nSTDOUT:\n'+run.stdout+'\nSTDERR:\n'+run.stderr,encoding='utf-8')
  print(run.stdout,run.stderr,flush=True)
  if run.returncode:raise RuntimeError('Invocation failed: '+name)
if __name__=='__main__':main()
