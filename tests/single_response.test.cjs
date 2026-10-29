'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { assess, makeRequest, main, RESPONSE_BYTES, GATEWAY, HARNESS_TIMEOUT_MS,
  remainingTimeout } = require('../scripts/single_response_harness.cjs');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');

const packet = {format:'single-response-v1', case_id:'example', input_hash:'a'.repeat(64),
  skill:'Read evidence. Return JSON.', report:{title:'Crash',body:'Traceback'},
  excerpts:[], omitted_context:[]};
const response = content => ({model:'reported-model', choices:[{
  finish_reason:'stop', message:{role:'assistant',content}}], usage:{prompt_tokens:10}});

test('deadline reserves cleanup time and subtracts time already spent in the step', () => {
  assert.equal(HARNESS_TIMEOUT_MS,540000);
  assert.equal(remainingTimeout(null,1000000),540000);
  assert.equal(remainingTimeout(1000000,1030000),510000);
  assert.equal(remainingTimeout(1000000,1600000),0);
  assert.throws(()=>remainingTimeout(1100000,1000000));
});

test('one fixed-gateway request contains the actual skill and no tools', async () => {
  let calls=0;
  const result=await assess(packet, async (url, options) => {
    calls++;
    assert.equal(url, GATEWAY);
    assert.equal(options.redirect, 'error');
    const body=JSON.parse(options.body);
    assert.equal(body.model, 'auto');
    assert.equal(Object.hasOwn(body,'tools'),false);
    assert.equal(Object.hasOwn(body,'tool_choice'),false);
    assert.ok(body.messages[0].content.includes(packet.skill));
    assert.equal(body.messages.length,2);
    return new Response(JSON.stringify(response('{"decision":"sufficient"}')));
  });
  assert.equal(calls,1);
  assert.equal(result.content,'{"decision":"sufficient"}');
});

test('request supplies a closed JSON contract with evidence identifiers as a string array', () => {
  const system=makeRequest({...packet,supplemental_context:{tool_result:'untrusted'},
    excerpts:[{key:'src/example.py'}]}).messages[0].content;
  const schema=JSON.parse(system.split('Output contract (JSON Schema):\n')[1]);
  assert.equal(schema.additionalProperties,false);
  assert.deepEqual(schema.required.sort(),['case_id','input_hash','decision','missing',
    'evidence','reasoning','questions','comment'].sort());
  assert.equal(schema.properties.case_id.const,packet.case_id);
  assert.equal(schema.properties.input_hash.const,packet.input_hash);
  assert.equal(schema.properties.evidence.type,'array');
  assert.equal(schema.properties.evidence.items.type,'string');
  assert.deepEqual(schema.properties.evidence.items.enum,['issue','tool_result','src/example.py']);
  assert.match(system,/Do not copy evidence objects/);
});

test('provider rejects a tool selector without nonempty tool definitions', async () => {
  let calls=0;
  const result=await assess(packet,async(_url,options)=>{
    calls++;
    const body=JSON.parse(options.body);
    if ('tool_choice' in body && !body.tools?.length) {
      return new Response(JSON.stringify({error:{code:'invalid_request_body',
        message:'tools are required when tool choice is specified'}}),{status:400});
    }
    return new Response(JSON.stringify(response('{}')));
  });
  assert.equal(result.content,'{}');
  assert.equal(calls,1);
});

for (const [name, value] of [
  ['tool call', {choices:[{finish_reason:'tool_calls',message:{content:'',tool_calls:[{}]}}]}],
  ['multiple responses', {choices:[response('{}').choices[0],response('{}').choices[0]]}],
  ['truncation', {choices:[{finish_reason:'length',message:{content:'{}'}}]}],
  ['empty output', response('')],
]) test(`${name} fails without a repair request`, async () => {
  let calls=0;
  await assert.rejects(assess(packet,async()=>{
    calls++; return new Response(JSON.stringify(value));
  }));
  assert.equal(calls,1);
});

test('429 is terminal and not retried', async () => {
  let calls=0;
  await assert.rejects(assess(packet,async()=>{
    calls++;return new Response('{}',{status:429});
  }), /429/);
  assert.equal(calls,1);
});

test('oversized response is rejected', async () => {
  await assert.rejects(assess(packet,async()=>new Response('x'.repeat(RESPONSE_BYTES+1))), /large/);
});

test('timeout aborts the sole request without retry', async () => {
  let calls=0;
  await assert.rejects(assess(packet,async(_url,options)=>{
    calls++;
    await new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('aborted')),{once:true}));
  },10), /timeout/);
  assert.equal(calls,1);
});

test('oversized packet fails before network', async () => {
  let calls=0;
  await assert.rejects(assess({...packet,report:{body:'x'.repeat(32769)}},async()=>{calls++;}));
  assert.equal(calls,0);
  assert.equal(makeRequest(packet).model,'auto');
});

test('trusted harness captures raw success and raw failure without another request', async () => {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'single-response-test-'));
  const oldFetch=global.fetch;
  const oldEnv={...process.env};
  const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
  try {
    for (const fail of [false,true]) {
      const workspace=path.join(root,String(fail));
      fs.mkdirSync(path.join(workspace,'input'),{recursive:true});
      const bytes=Buffer.from(JSON.stringify(packet));
      fs.writeFileSync(path.join(workspace,'input/packet.json'),bytes);
      fs.writeFileSync(path.join(workspace,'input/manifest.json'),JSON.stringify({
        packet_sha256:sha(bytes),skill_sha256:sha(packet.skill),
        case_id:packet.case_id,input_hash:packet.input_hash}));
      process.env.GITHUB_WORKSPACE=workspace;
      process.env.GH_AW_SAFE_OUTPUTS=path.join(workspace,'safeoutputs/outputs.jsonl');
      const stepStartFile=path.join(workspace,'step-start.txt');
      fs.writeFileSync(stepStartFile,String(Date.now()));
      let calls=0;
      const raw=fail ? '{invalid JSON' : JSON.stringify(response('{}'));
      global.fetch=async()=>{calls++;return new Response(raw);};
      if (fail) await assert.rejects(main({stepStartFile})); else await main({stepStartFile});
      assert.equal(calls,1);
      assert.equal(fs.readFileSync(path.join(workspace,'output/provider-response.json'),'utf8'),raw);
      const trace=JSON.parse(fs.readFileSync(path.join(workspace,'output/execution.json'),'utf8'));
      assert.equal(trace.requests_sent,1);
      assert.equal(trace.status,fail?'failed':'response_received');
      const request=JSON.parse(fs.readFileSync(path.join(workspace,'output/request.json'),'utf8'));
      assert.ok(request.messages[0].content.includes(packet.skill));
      await assert.rejects(main({stepStartFile}),/already recorded/);
      assert.equal(calls,1);
    }
  } finally {
    global.fetch=oldFetch;
    for (const key of Object.keys(process.env)) if (!(key in oldEnv)) delete process.env[key];
    Object.assign(process.env,oldEnv);
    assert.ok(path.resolve(root).startsWith(path.resolve(os.tmpdir())+path.sep));
    fs.rmSync(root,{recursive:true,force:true});
  }
});

test('successful inference never writes the read-only framework safe-output path', async () => {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'single-response-readonly-'));
  const oldEnv={...process.env};
  const originalWrite=fs.writeFileSync;
  const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
  try {
    fs.mkdirSync(path.join(root,'input'));
    const bytes=Buffer.from(JSON.stringify(packet));
    fs.writeFileSync(path.join(root,'input/packet.json'),bytes);
    fs.writeFileSync(path.join(root,'input/manifest.json'),JSON.stringify({
      packet_sha256:sha(bytes),skill_sha256:sha(packet.skill),
      case_id:packet.case_id,input_hash:packet.input_hash}));
    const stepStartFile=path.join(root,'step-start.txt');
    fs.writeFileSync(stepStartFile,String(Date.now()));
    const safe=path.join(root,'safeoutputs/outputs.jsonl');
    fs.mkdirSync(path.dirname(safe));
    process.env.GITHUB_WORKSPACE=root;
    process.env.GH_AW_SAFE_OUTPUTS=safe;
    fs.writeFileSync=(destination,...args)=>{
      if (destination===safe) throw Object.assign(new Error('read-only file system'),{code:'EROFS'});
      return originalWrite(destination,...args);
    };
    let calls=0;
    await main({stepStartFile,transport:async()=>{
      calls++;return new Response(JSON.stringify(response('{"evidence":["issue"]}')));
    }});
    assert.equal(calls,1);
    const trace=JSON.parse(fs.readFileSync(path.join(root,'output/execution.json'),'utf8'));
    assert.equal(trace.status,'response_received');
    assert.equal(trace.model_reported,'reported-model');
    assert.equal(fs.existsSync(safe),false);
    assert.equal(fs.readFileSync(path.join(root,'output/recommendation.json'),'utf8'),
      '{"evidence":["issue"]}');
  } finally {
    fs.writeFileSync=originalWrite;
    for (const key of Object.keys(process.env)) if (!(key in oldEnv)) delete process.env[key];
    Object.assign(process.env,oldEnv);
    assert.ok(path.resolve(root).startsWith(path.resolve(os.tmpdir())+path.sep));
    fs.rmSync(root,{recursive:true,force:true});
  }
});

test('harness timeout persists failed evidence before the outer deadline', async () => {
  assert.equal(HARNESS_TIMEOUT_MS,540000);
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'single-response-timeout-'));
  const oldEnv={...process.env};
  const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
  try {
    fs.mkdirSync(path.join(root,'input'));
    const bytes=Buffer.from(JSON.stringify(packet));
    fs.writeFileSync(path.join(root,'input/packet.json'),bytes);
    fs.writeFileSync(path.join(root,'input/manifest.json'),JSON.stringify({
      packet_sha256:sha(bytes),skill_sha256:sha(packet.skill),
      case_id:packet.case_id,input_hash:packet.input_hash}));
    process.env.GITHUB_WORKSPACE=root;
    let calls=0;
    const transport=async(_url,options)=>{
      calls++;
      await new Promise((_,reject)=>options.signal.addEventListener('abort',
        ()=>reject(new Error('aborted')),{once:true}));
    };
    const stepStartFile=path.join(root,'step-start.txt');
    fs.writeFileSync(stepStartFile,String(Date.now()));
    await assert.rejects(main({transport,timeoutMs:10,stepStartFile}),/timeout/);
    const trace=JSON.parse(fs.readFileSync(path.join(root,'output/execution.json'),'utf8'));
    assert.equal(calls,1);
    assert.equal(trace.status,'failed');
    assert.match(trace.error,/timeout/);
    assert.equal(trace.requests_sent,1);
    assert.equal(trace.timeout_ms,10);
    const missing=path.join(root,'missing-clock');
    fs.mkdirSync(path.join(missing,'input'),{recursive:true});
    for (const name of ['packet.json','manifest.json']) {
      fs.copyFileSync(path.join(root,'input',name),path.join(missing,'input',name));
    }
    process.env.GITHUB_WORKSPACE=missing;
    await assert.rejects(main({transport,stepStartFile:path.join(missing,'absent')}),/timestamp missing/);
    const refused=JSON.parse(fs.readFileSync(path.join(missing,'output/execution.json'),'utf8'));
    assert.equal(refused.status,'failed');
    assert.equal(refused.requests_sent,0);
    assert.equal(calls,1); // Missing deadline metadata did not make another request.
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in oldEnv)) delete process.env[key];
    Object.assign(process.env,oldEnv);
    assert.ok(path.resolve(root).startsWith(path.resolve(os.tmpdir())+path.sep));
    fs.rmSync(root,{recursive:true,force:true});
  }
});
