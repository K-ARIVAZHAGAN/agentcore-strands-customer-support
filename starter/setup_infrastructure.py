"""Provision the course's demo resources; checkpoint IDs for resumable setup."""
import boto3,io,json,time,zipfile
from pathlib import Path
from botocore.exceptions import ClientError
REGION='us-east-1'
root=Path(__file__).resolve().parent
state_path=root/'project_resources.json'
state=json.loads(state_path.read_text()) if state_path.exists() else {'region':REGION}
session=boto3.Session(region_name=REGION)
def save():state_path.write_text(json.dumps(state,indent=2)+'\n')
def wait(get,field,ready):
 for _ in range(60):
  r=get();s=r[field];print(field,s,flush=True)
  if s==ready:return r
  if s in ('FAILED','CREATE_FAILED','DELETE_FAILED'):raise RuntimeError(str(r))
  time.sleep(10)
 raise TimeoutError('Resource did not become ready')
def role(name,service,statements):
 iam=session.client('iam')
 try:r=iam.get_role(RoleName=name)['Role']
 except iam.exceptions.NoSuchEntityException:r=iam.create_role(RoleName=name,AssumeRolePolicyDocument=json.dumps({'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':service},'Action':'sts:AssumeRole'}]}))['Role']
 if statements:iam.put_role_policy(RoleName=name,PolicyName='CourseProjectAccess',PolicyDocument=json.dumps({'Version':'2012-10-17','Statement':statements}))
 return r['Arn']
def main():
 account=session.client('sts').get_caller_identity()['Account'];state['account']=account;save()
 iam=session.client('iam');lam=session.client('lambda');api=session.client('apigateway');control=session.client('bedrock-agentcore-control');bedrock=session.client('bedrock-agent');s3=session.client('s3')
 execution=role('csai-demo-lambda-role','lambda.amazonaws.com',[{'Effect':'Allow','Action':['logs:CreateLogGroup','logs:CreateLogStream','logs:PutLogEvents'],'Resource':f'arn:aws:logs:{REGION}:{account}:*'}])
 time.sleep(10)
 for name,file in [('order-tracker','order_tracker.py'),('refund-processor','refund_processor.py')]:
  if name in state:continue
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:z.writestr('index.py',(root/'lambda'/file).read_bytes())
  try:r=lam.get_function(FunctionName=name)['Configuration']
  except lam.exceptions.ResourceNotFoundException:r=lam.create_function(FunctionName=name,Runtime='python3.12',Role=execution,Handler='index.lambda_handler',Code={'ZipFile':data.getvalue()},Timeout=30,MemorySize=128)
  state[name]=r['FunctionArn'];save();print('Lambda ready:',name,flush=True)
 if 'rest_api_id' not in state:
  # Import a proxy-integrated OpenAPI document; no real customer data is used.
  paths={}
  for path,operation,param in [('/orders/{order_id}','get_order','order_id'),('/customers/{customer_id}/orders','get_customer_orders','customer_id'),('/customers/{customer_id}','get_customer','customer_id')]:
   paths[path]={'get':{'operationId':operation,'parameters':[{'name':param,'in':'path','required':True,'type':'string'}],'responses':{'200':{'description':'Demo JSON response'}},'x-amazon-apigateway-integration':{'type':'aws_proxy','httpMethod':'POST','uri':f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{state['order-tracker']}/invocations"}}}
  spec={'swagger':'2.0','info':{'title':'csai-demo-orders','version':'1.0'},'schemes':['https'],'paths':paths}
  r=api.import_rest_api(body=json.dumps(spec).encode());state['rest_api_id']=r['id'];save()
  lam.add_permission(FunctionName='order-tracker',StatementId='csai-api-proxy',Action='lambda:InvokeFunction',Principal='apigateway.amazonaws.com',SourceArn=f"arn:aws:execute-api:{REGION}:{account}:{r['id']}/*")
  api.create_deployment(restApiId=r['id'],stageName='prod')
 gateway_role=role('csai-demo-gateway-role','bedrock-agentcore.amazonaws.com',[{'Effect':'Allow','Action':'lambda:InvokeFunction','Resource':state['refund-processor']},{'Effect':'Allow','Action':['execute-api:Invoke','apigateway:GET'],'Resource':[f"arn:aws:execute-api:{REGION}:{account}:{state['rest_api_id']}/*",f"arn:aws:apigateway:{REGION}::/restapis/{state['rest_api_id']}/*"]}])
 if 'gateway_id' not in state:
  time.sleep(10)
  r=control.create_gateway(name='CustomerSupportGateway',roleArn=gateway_role,protocolType='MCP',authorizerType='NONE')
  state.update(gateway_id=r['gatewayId'],gateway_url=r['gatewayUrl']);save()
 wait(lambda:control.get_gateway(gatewayIdentifier=state['gateway_id']),'status','READY')
 if 'order_target' not in state:
  r=control.create_gateway_target(gatewayIdentifier=state['gateway_id'],name='order-tracker',targetConfiguration={'mcp':{'apiGateway':{'restApiId':state['rest_api_id'],'stage':'prod','apiGatewayToolConfiguration':{'toolFilters':[{'filterPath':'/*','methods':['GET']}],'toolOverrides':[{'name':op,'path':path,'method':'GET'} for path,op in [('/orders/{order_id}','get_order'),('/customers/{customer_id}/orders','get_customer_orders'),('/customers/{customer_id}','get_customer')]]}}}},credentialProviderConfigurations=[{'credentialProviderType':'GATEWAY_IAM_ROLE'}])
  state['order_target']=r['targetId'];save()
 if 'refund_target' not in state:
  r=control.create_gateway_target(gatewayIdentifier=state['gateway_id'],name='refund-processor',targetConfiguration={'mcp':{'lambda':{'lambdaArn':state['refund-processor'],'toolSchema':{'inlinePayload':json.loads((root/'lambda/lambda_schema').read_text())}}}},credentialProviderConfigurations=[{'credentialProviderType':'GATEWAY_IAM_ROLE'}]);state['refund_target']=r['targetId'];save()
 bucket=f'csai-demo-catalog-{account}'
 if 'bucket' not in state:
  try:s3.head_bucket(Bucket=bucket)
  except ClientError:s3.create_bucket(Bucket=bucket)
  s3.put_public_access_block(Bucket=bucket,PublicAccessBlockConfiguration={'BlockPublicAcls':True,'IgnorePublicAcls':True,'BlockPublicPolicy':True,'RestrictPublicBuckets':True})
  s3.upload_file(str(root/'product_catalog.txt'),bucket,'product_catalog.txt');state['bucket']=bucket;save()
 kb_role=role('csai-demo-kb-role','bedrock.amazonaws.com',[{'Effect':'Allow','Action':'s3:ListBucket','Resource':f'arn:aws:s3:::{bucket}'},{'Effect':'Allow','Action':'s3:GetObject','Resource':f'arn:aws:s3:::{bucket}/*'}])
 if 'kb_id' not in state:
  time.sleep(10)
  r=bedrock.create_knowledge_base(name='CustomerSupportKB',roleArn=kb_role,knowledgeBaseConfiguration={'type':'MANAGED','managedKnowledgeBaseConfiguration':{'embeddingModelType':'MANAGED'}})
  state['kb_id']=r['knowledgeBase']['knowledgeBaseId'];save()
 wait(lambda:bedrock.get_knowledge_base(knowledgeBaseId=state['kb_id'])['knowledgeBase'],'status','ACTIVE')
 if 'data_source_id' not in state:
  r=bedrock.create_data_source(knowledgeBaseId=state['kb_id'],name='product-catalog',dataSourceConfiguration={'type':'MANAGED_KNOWLEDGE_BASE_CONNECTOR','managedKnowledgeBaseConnectorConfiguration':{'connectorParameters':{'type':'S3','version':'1','connectionConfiguration':{'bucketName':bucket,'bucketOwnerAccountId':account},'deletionProtectionConfiguration':{'enableDeletionProtection':False}}}}, vectorIngestionConfiguration={'parsingConfiguration':{'parsingStrategy':'SMART_PARSING'}});state['data_source_id']=r['dataSource']['dataSourceId'];save()
 wait(lambda:bedrock.get_data_source(knowledgeBaseId=state['kb_id'],dataSourceId=state['data_source_id'])['dataSource'],'status','AVAILABLE')
 if 'ingestion_job_id' not in state:
  r=bedrock.start_ingestion_job(knowledgeBaseId=state['kb_id'],dataSourceId=state['data_source_id']);state['ingestion_job_id']=r['ingestionJob']['ingestionJobId'];save()
 if 'memory_id' not in state:
  r=control.create_memory(name='CustomerSupportMemory',eventExpiryDuration=7,memoryStrategies=[{'semanticMemoryStrategy':{'name':'customer_facts','namespaceTemplates':['cs_agent/{actorId}/facts']}},{'userPreferenceMemoryStrategy':{'name':'customer_preferences','namespaceTemplates':['cs_agent/{actorId}/preferences']}}]);state['memory_id']=r['memory']['id'];save()
 wait(lambda:control.get_memory(memoryId=state['memory_id'])['memory'],'status','ACTIVE')
 source=(root/'main.py').read_text(encoding='utf-8-sig')
 import re
 for key,value in [('GATEWAY_URL',state['gateway_url']),('KB_ID',state['kb_id']),('MEMORY_ID',state['memory_id'])]:source=re.sub(r'^'+key+r' = .*$',key+' = '+json.dumps(value),source,flags=re.M)
 (root/'main.py').write_text(source,encoding='utf-8');print('Infrastructure ready and main.py configured.',flush=True)
 wait(lambda:bedrock.get_ingestion_job(knowledgeBaseId=state['kb_id'],dataSourceId=state['data_source_id'],ingestionJobId=state['ingestion_job_id'])['ingestionJob'],'status','COMPLETE')

if __name__=='__main__':main()
