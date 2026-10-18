"""Offline checks of real business rules and memory behavior; no AWS calls."""
import contextlib,io,json,os,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
os.environ.setdefault('AWS_ACCESS_KEY_ID','offline-check')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY','offline-check')
import main

class Checks(unittest.TestCase):
 def test_reference_calculation(self):
  r=main.loyalty_breakdown(4250,'Gold',150,'standard')
  self.assertEqual((r['points_redeemed'],r['tier_discount_pct'],r['final_total'],r['remaining_points']),(4000,10,'99.00',349))
 def test_redemption_cap_and_rounding(self):
  r=main.loyalty_breakdown(100000,'Platinum','19.99','device')
  self.assertEqual(r['points_redeemed'],500)
  self.assertEqual(r['final_total'],'12.74')
  self.assertEqual(main.loyalty_breakdown(499,'Silver',10,'fresh')['points_redeemed'],0)
 def test_namespace_compatibility(self):
  c=Mock();c.get_memory_strategies.return_value=[{'type':'SEMANTIC','namespaceTemplates':['cs/{actorId}/facts']},{'type':'USER_PREFERENCE','namespaces':['cs/{actorId}/preferences']}]
  self.assertEqual(len(main.get_namespaces(c,'memory')),2)
 def test_memory_original_text_and_tool_exclusion(self):
  c=Mock();c.get_memory_strategies.return_value=[{'type':'SEMANTIC','namespaceTemplates':['cs/{actorId}/facts']}]
  c.retrieve_memories.return_value=[{'content':{'text':'Prefers short answers'}}]
  h=main.MemoryHook('customer-a','session-a',c,'memory')
  msg={'role':'user','content':[{'text':'Track my order'}]}; agent=SimpleNamespace(messages=[msg]);event=SimpleNamespace(agent=agent)
  h.retrieve_customer_context(event)
  self.assertIn('[SEMANTIC]',msg['content'][0]['text'])
  self.assertEqual(c.retrieve_memories.call_args.kwargs['namespace'],'cs/customer-a/facts')
  agent.messages.append({'role':'assistant','content':[{'text':'Which order?'}]});h.save_support_interaction(event)
  self.assertEqual(c.create_event.call_args.kwargs['messages'][0],('Track my order','USER'))
  c.retrieve_memories.reset_mock();agent.messages.append({'role':'user','content':[{'toolResult':{'toolUseId':'x','content':[]}}]});h.retrieve_customer_context(event);c.retrieve_memories.assert_not_called()
 def test_code_interpreter_self_contained(self):
  def execute(method,args):
   self.assertEqual(method,'executeCode');self.assertTrue(args['clearContext'])
   out=io.StringIO()
   with contextlib.redirect_stdout(out):exec(args['code'],{})
   return {'stream':[{'result':{'content':[{'type':'text','text':out.getvalue()}]}}]}
  cm=Mock();cm.__enter__=Mock(return_value=SimpleNamespace(invoke=execute));cm.__exit__=Mock(return_value=False)
  with patch.object(main,'code_session',return_value=cm):r=json.loads(main.calculate_loyalty_discount(4250,'Gold',150))
  self.assertEqual(r['execution'],'agentcore_code_interpreter');self.assertEqual(r['final_total'],'99.00')
 def test_fallback_is_disclosed(self):
  with patch.object(main,'code_session',side_effect=RuntimeError('offline')):r=json.loads(main.calculate_loyalty_discount(4250,'Gold',150))
  self.assertEqual(r['execution'],'tier_only_fallback');self.assertEqual(r['points_redeemed'],0);self.assertEqual(r['final_total'],'135.00')
 def test_kb_guard_and_join(self):
  with patch.object(main,'KB_ID',''):self.assertIn('not configured',main.search_knowledge_base('policy'))
  client=Mock();client.retrieve.return_value={'retrievalResults':[{'content':{'text':'first'}},{'content':{'text':'second'}}]}
  with patch.object(main,'KB_ID','1234567890'),patch.object(main,'_bedrock_runtime',client):self.assertEqual(main.search_knowledge_base('policy'),'first\n---\nsecond')

 def test_browser_driver_recovery_does_not_modify_dependency(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'packaged-node';source.write_bytes(b'test fixture')
   environment={}
   fake_os=SimpleNamespace(name='posix',access=lambda path,mode:False,X_OK=1,environ=environment)
   with patch.object(main,'os',fake_os),patch('playwright._impl._driver.compute_driver_executable',return_value=(str(source),'cli.js')),patch('tempfile.gettempdir',return_value=directory):
    main.prepare_browser_driver()
   destination=Path(environment['PLAYWRIGHT_NODEJS_PATH'])
   self.assertNotEqual(source,destination)
   self.assertEqual(destination.read_bytes(),b'test fixture')
   self.assertEqual(source.read_bytes(),b'test fixture')

if __name__=='__main__':unittest.main()
