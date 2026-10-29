'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { assess, makeRequest, main, RESPONSE_BYTES, GATEWAY } = require('../scripts/single_response_harness.cjs');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');

const packet = {format:'single-response-v1', case_id:'example', input_hash:'a'.repeat(64),
  skill:'Read evidence. Return JSON.', report:{title:'Crash',body:'Traceback'},
  excerpts:[], omitted_context:[]};
const response = content => ({model:'reported-model', choices:[{
  finish_reason:'stop', message:{role:'assistant',content}}], usage:{prompt_tokens:10}});

test('one fixed-gateway request contains the actual skill and no tools', async () => {
  let calls=0;
  const result=await assess(packet, async (url, options) => {
    calls++;
    assert.equal(url, GATEWAY);
    assert.equal(options.redirect, 'error');
    const body=JSON.parse(options.body);
    assert.equal(body.model, 'auto');
    assert.deepEqual(body.tools, []);
    assert.equal(body.tool_choice, 'none');
    assert.ok(body.messages[0].content.includes(packet.skill));
    assert.equal(body.messages.length,2);
    return new Response(JSON.stringify(response('{"decision":"sufficient"}')));
  });
  assert.equal(calls,1);
  assert.equal(result.content,'{"decision":"sufficient"}');
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
  },10), /aborted/);
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
      let calls=0;
      const raw=fail ? '{invalid JSON' : JSON.stringify(response('{}'));
      global.fetch=async()=>{calls++;return new Response(raw);};
      if (fail) await assert.rejects(main()); else await main();
      assert.equal(calls,1);
      assert.equal(fs.readFileSync(path.join(workspace,'output/provider-response.json'),'utf8'),raw);
      const trace=JSON.parse(fs.readFileSync(path.join(workspace,'output/execution.json'),'utf8'));
      assert.equal(trace.requests_sent,1);
      assert.equal(trace.status,fail?'failed':'response_received');
      const request=JSON.parse(fs.readFileSync(path.join(workspace,'output/request.json'),'utf8'));
      assert.ok(request.messages[0].content.includes(packet.skill));
      await assert.rejects(main(),/already recorded/);
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
