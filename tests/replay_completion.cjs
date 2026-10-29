'use strict';
// Offline diagnostic only: official pinned bridge/collector plus a loopback MCP fixture.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {Worker}=require('node:worker_threads');
const {execFileSync}=require('node:child_process');
const crypto=require('node:crypto');
const repo=process.cwd();
assert.equal(process.argv.length,5,'Usage: node tests/replay_completion.cjs PINNED_RUNTIME SAVED_PROVIDER_RESPONSE PACKET');
const runtime=path.resolve(process.argv[2]);
const savedResponse=path.resolve(process.argv[3]);
const packetFile=path.resolve(process.argv[4]);
const pinnedHashes={
 'mcp_cli_bridge.cjs':'eda43cc6e93f63ba91d014b30faaeb5b8d8c95ac5536edd9adfc56407c9faf8d',
 'collect_ndjson_output.cjs':'ed4118298f20d02b89c5239337581b53945a1b1b5ccee91ba4ec5e20174f5d46',
 'handle_agent_failure.cjs':'0c429a3e426995ecc1aa178db5e95464534e2c9ccd8c463fc54508629326fe25'};
for(const [name,expected] of Object.entries(pinnedHashes)) {
 assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(runtime,name))).digest('hex'),expected,
  `Pinned framework source changed: ${name}`);
}
const root=fs.mkdtempSync(path.resolve('.local/completion-replay-'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const errors=[];
const outputs={};
global.core={info:()=>{},debug:()=>{},warning:()=>{},notice:()=>{},error:x=>errors.push(String(x)),
  setFailed:x=>errors.push(String(x)),setOutput:(k,v)=>{outputs[k]=v;},
  exportVariable:(k,v)=>{process.env[k]=v;}};
require(path.join(runtime,'constants.cjs')).TMP_GH_AW_PATH=path.join(root,'framework');
const collector=require(path.join(runtime,'collect_ndjson_output.cjs'));
const conclusion=require(path.join(runtime,'handle_agent_failure.cjs'));
process.env.GH_AW_AGENT_CONCLUSION='success';
process.env.GH_AW_FAILURE_REPORT_AS_ISSUE='false';
global.context={repo:{owner:'offline',repo:'fixture'},payload:{},runId:0,eventName:'workflow_dispatch'};
let externalCalls=0;
const blockedClient=new Proxy(()=>{}, {
 get(){return blockedClient;},apply(){externalCalls++;throw new Error('GitHub network calls forbidden in replay');}});
global.github=blockedClient;
const {main,emitCompletion}=require(path.resolve('scripts/single_response_harness.cjs'));
const safe=path.join(root,'runner/gh-aw/safeoutputs/outputs.jsonl');
process.env.RUNNER_TEMP=path.join(root,'runner');
process.env.GH_AW_SAFE_OUTPUTS=safe;
process.env.GH_AW_SAFE_OUTPUTS_CONFIG_PATH=path.join(root,'safe-config.json');
fs.mkdirSync(path.dirname(safe),{recursive:true});
fs.writeFileSync(process.env.GH_AW_SAFE_OUTPUTS_CONFIG_PATH,JSON.stringify({noop:{max:2}}));
const tool={name:'noop',inputSchema:{type:'object',properties:{message:{type:'string'}},required:['message']}};
const toolsFile=path.join(root,'tools.json');
fs.writeFileSync(toolsFile,JSON.stringify([tool]));
const worker=new Worker(`
const {parentPort,workerData}=require('node:worker_threads');
const http=require('node:http'),fs=require('node:fs');
let calls=0;
http.createServer((req,res)=>{
 let bytes='';req.on('data',x=>bytes+=x);req.on('end',()=>{
  const data=JSON.parse(bytes);let result={};
  if(data.method==='initialize') result={protocolVersion:'2024-11-05',capabilities:{tools:{}},serverInfo:{name:'offline-fixture',version:'1'}};
  else if(data.method==='tools/call'){
   calls++;
   if(data.params.name!=='noop') throw new Error('unexpected tool');
   const item={type:'noop',...data.params.arguments};
   fs.appendFileSync(workerData.safe,JSON.stringify(item)+'\\n');
   result={content:[{type:'text',text:'No-op recorded.'}]};
   parentPort.postMessage({calls,item});
  }
  res.writeHead(data.id===undefined?202:200,{'content-type':'application/json','mcp-session-id':'offline-session'});
  res.end(data.id===undefined?'':JSON.stringify({jsonrpc:'2.0',id:data.id,result}));
 });
}).listen(0,'127.0.0.1',function(){parentPort.postMessage({port:this.address().port});});
`,{eval:true,workerData:{safe}});
let gatewayCall;
worker.on('message',message=>{if(message.item) gatewayCall=message;});
(async()=>{
 try {
  const port=await new Promise((resolve,reject)=>{
   worker.on('message',x=>{if(x.port)resolve(x.port);});worker.on('error',reject);
  });
  await collector.main();
  const absent=JSON.parse(outputs.output);
  assert.equal(absent.collectorFailureCause,'missing_terminal_safe_output');
  await conclusion.main();
  assert.ok(errors.some(x=>x.includes('could not complete the task')));
  const negativeConclusionErrors=[...errors];
  const negativeBlockedApiCalls=externalCalls;
  errors.length=0;
  const bytes=fs.readFileSync(packetFile);
  const packet=JSON.parse(bytes);
  const workspace=path.join(root,'workspace');
  fs.mkdirSync(path.join(workspace,'input'),{recursive:true});
  fs.writeFileSync(path.join(workspace,'input/packet.json'),bytes);
  fs.writeFileSync(path.join(workspace,'input/manifest.json'),JSON.stringify({
   case_id:packet.case_id,input_hash:packet.input_hash,packet_sha256:sha(bytes),skill_sha256:sha(packet.skill)}));
  process.env.GITHUB_WORKSPACE=workspace;
  const stepStartFile=path.join(root,'start.txt');fs.writeFileSync(stepStartFile,String(Date.now()));
  const saved=fs.readFileSync(savedResponse,'utf8');
  let providerCalls=0,completionCalls=0;
  const originalWrite=fs.writeFileSync;
  fs.writeFileSync=(destination,...args)=>{
   if(destination===safe) throw Object.assign(new Error('read-only framework path'),{code:'EROFS'});
   return originalWrite(destination,...args);
  };
  try {
   await main({stepStartFile,transport:async()=>{providerCalls++;return new Response(saved);},
    emitCompletion:()=>emitCompletion((file,args,options)=>{
     completionCalls++;
     assert.equal(file,path.join(process.env.RUNNER_TEMP,'gh-aw/mcp-cli/bin/safeoutputs'));
     return execFileSync(process.execPath,[path.join(runtime,'mcp_cli_bridge.cjs'),
      '--server-name','safeoutputs','--server-url',`http://127.0.0.1:${port}/safeoutputs`,
      '--tools-file',toolsFile,'--api-key','offline-fixture-key',...args],options);
    })});
  } finally {fs.writeFileSync=originalWrite;}
  await new Promise(resolve=>setTimeout(resolve,20));
  assert.equal(providerCalls,1);assert.equal(completionCalls,1);assert.equal(gatewayCall.calls,1);
  assert.equal(gatewayCall.item.type,'noop');
  await collector.main();
  const final=JSON.parse(outputs.output);
  assert.equal(final.collectorFailureCause,undefined);
  assert.equal(final.items.length,1);assert.equal(final.items[0].type,'noop');
  assert.deepEqual(final.errors,[]);
  await conclusion.main();
  assert.deepEqual(errors,[]);
  assert.equal(externalCalls,negativeBlockedApiCalls);
  const recommendation=fs.readFileSync(path.join(workspace,'output/recommendation.json'));
  assert.equal(recommendation.toString(),JSON.parse(saved).choices[0].message.content);
  const report={source_commit:'32ecafbc061c9af57e9361942099e381102ae304',
   source_sha256:pinnedHashes,saved_provider_response_sha256:sha(saved),
   provider_requests_replayed:providerCalls,new_ai_requests:0,
   completion_calls:completionCalls,direct_protected_writes:0,negative_collector_cause:absent.collectorFailureCause,
   positive_collector_items:final.items,positive_collector_errors:final.errors,
   negative_conclusion_errors:negativeConclusionErrors,positive_conclusion_errors:[...errors],
   external_github_requests:0,negative_blocked_api_calls:negativeBlockedApiCalls,positive_api_calls:externalCalls-negativeBlockedApiCalls,
   recommendation_sha256:sha(recommendation),recommendation_unchanged:true,
   limitations:['MCP server is a loopback fixture; actual Docker wrapper/mounts and hosted job orchestration remain untested.']};
  fs.writeFileSync(path.resolve('evals/evidence/completion-replay-result.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
 } finally {
  await worker.terminate();
  assert.ok(root.startsWith(path.join(repo,'.local')+path.sep));
  fs.rmSync(root,{recursive:true,force:true});
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
