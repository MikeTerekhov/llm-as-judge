"use client";
import {useState} from "react";
import Link from "next/link";
import "./history.css";

const LABELS=["supported","contradicted","insufficient_evidence"] as const;
type Label=typeof LABELS[number];
type Row={example_id:string;expected:Label;model_verdict:Label|null};
type Run={mode:string;model:string;report:{total:number;rows:Row[]}};
type Entry={recorded_at:string;sha256:string;run:Run};
type History={schema_version:number;runs:Entry[]};
type Metric={date:string;model:string;coverage:number;agreement:number|null;f1:number|null;returned:number;id:string};
const pct=(n:number|null)=>n===null?"N/A":(100*n).toFixed(1)+"%";
function validate(raw:unknown):Entry[]{
  if(!raw||typeof raw!=="object")throw Error("Expected an AR-042 history JSON object.");
  const history=raw as Partial<History>;
  if(history.schema_version!==1||!Array.isArray(history.runs)||history.runs.length>200)throw Error("Unsupported history schema or run count.");
  const entries=history.runs;
  let reference:Map<string,Label>|null=null;
  for(const entry of entries){
    if(!entry||typeof entry.recorded_at!=="string"||!Number.isFinite(Date.parse(entry.recorded_at))||typeof entry.sha256!=="string"||!/^[a-f0-9]{64}$/.test(entry.sha256)||!entry.run||entry.run.mode!=="executed"||typeof entry.run.model!=="string"||!entry.run.model.trim()||entry.run.report?.total!==12||!Array.isArray(entry.run.report.rows)||entry.run.report.rows.length!==12)throw Error("History contains an invalid run.");
    const labels=new Map<string,Label>();
    for(const row of entry.run.report.rows){
      if(!row||typeof row.example_id!=="string"||!row.example_id||labels.has(row.example_id)||!LABELS.includes(row.expected)||!(row.model_verdict===null||LABELS.includes(row.model_verdict)))throw Error("History contains invalid or duplicate fixtures.");
      labels.set(row.example_id,row.expected);
    }
    if(reference&&([...reference].some(([id,label])=>labels.get(id)!==label)))throw Error("History contains mismatched benchmark fixtures.");
    reference=labels;
  }
  return entries.slice().sort((a,b)=>Date.parse(a.recorded_at)-Date.parse(b.recorded_at));
}
function metric(entry:Entry):Metric{
  const rows=entry.run.report.rows.filter(row=>row.model_verdict!==null);
  const correct=rows.filter(row=>row.expected===row.model_verdict).length;
  const f1s=LABELS.map(label=>{
    const tp=rows.filter(row=>row.expected===label&&row.model_verdict===label).length;
    const predicted=rows.filter(row=>row.model_verdict===label).length;
    const actual=rows.filter(row=>row.expected===label).length;
    const precision=predicted?tp/predicted:null,recall=actual?tp/actual:null;
    return precision!==null&&recall!==null&&precision+recall>0?2*precision*recall/(precision+recall):null;
  }).filter((x):x is number=>x!==null);
  return {date:entry.recorded_at,model:entry.run.model,coverage:rows.length/12,
          agreement:rows.length?correct/rows.length:null,
          f1:f1s.length?f1s.reduce((a,b)=>a+b,0)/f1s.length:null,
          returned:rows.length,id:entry.sha256};
}
export default function HistoryPage(){
  const [entries,setEntries]=useState<Entry[]>([]);
  const [error,setError]=useState("");
  const [model,setModel]=useState("all");
  const [selected,setSelected]=useState<string|null>(null);
  async function load(file:File|undefined){
    if(!file)return;
    try{
      if(file.size>2*1024*1024)throw Error("History file exceeds 2 MiB.");
      const parsed=validate(JSON.parse(await file.text()));
      setEntries(parsed);setError("");setModel("all");setSelected(null);
    }catch(e){setEntries([]);setError(e instanceof Error?e.message:"Could not read history file.");}
  }
  const models=[...new Set(entries.map(e=>e.run.model))].sort();
  const filtered=entries.filter(e=>model==="all"||e.run.model===model).map(metric);
  const current=entries.find(e=>e.sha256===selected);
  return <main className="history-dashboard">
    <p className="muted">AI REGIMEN / SYNTHETIC RESEARCH</p>
    <h1>Experiment history</h1>
    <p>Explore model benchmark performance across recorded runs. Import an AR-042 local history file; processing stays in your browser, with no uploads or model calls.</p>
    <p><Link href="/judge/overview">Research overview</Link> · <Link href="/judge/model-comparison">Compare individual runs</Link></p>
    <section className="panel"><h2>Load saved history</h2><label htmlFor="history-file">AR-042 history JSON (up to 2 MiB)</label><input id="history-file" type="file" accept=".json,application/json" onChange={e=>void load(e.target.files?.[0])}/>{error&&<p role="alert" className="notice">{error}</p>}<p className="muted">Generate this file using the local experiment-history CLI. The browser does not access your local filesystem automatically.</p></section>
    {entries.length>0&&<>
      <section className="panel"><h2>Recorded runs</h2><div className="history-stats"><article><strong>{entries.length}</strong><span>Runs</span></article><article><strong>{models.length}</strong><span>Model identifiers</span></article><article><strong>{filtered.length}</strong><span>Filtered runs</span></article></div>
      <label htmlFor="history-model">Filter model</label><select id="history-model" value={model} onChange={e=>{setModel(e.target.value);setSelected(null);}}><option value="all">All models</option>{models.map(name=><option key={name} value={name}>{name}</option>)}</select></section>
      <section className="panel"><h2>Agreement over time</h2><p className="muted">Conditional agreement with fictional authored labels. Missing verdicts are excluded, not scored as incorrect.</p>
        <div className="history-chart" role="img" aria-label="Chronological agreement percentages for returned model verdicts">{filtered.map((item,i)=><div className="history-bar" key={item.id} title={item.model+" — "+item.date+" — "+pct(item.agreement)}><div className="history-bar-space"><div style={{height:pct(item.agreement===null?0:item.agreement)}}/></div><small>{i+1}</small></div>)}</div>
        <p className="muted">Bars follow chronological run order. A missing bar means agreement was unavailable; use the table for exact dates and coverage.</p>
      </section>
      <section className="panel"><h2>Run history</h2><div className="history-scroll"><table><thead><tr><th>Date (UTC)</th><th>Model</th><th>Verdicts</th><th>Coverage</th><th>Agreement</th><th>Macro F1</th><th>Details</th></tr></thead><tbody>{filtered.map(item=><tr key={item.id}><td>{new Date(item.date).toISOString().slice(0,16).replace("T"," ")}</td><td>{item.model}</td><td>{item.returned}/12</td><td>{pct(item.coverage)}</td><td>{pct(item.agreement)}</td><td>{item.f1===null?"N/A":item.f1.toFixed(3)}</td><td><button onClick={()=>setSelected(item.id===selected?null:item.id)}>{item.id===selected?"Close":"Inspect"}</button></td></tr>)}</tbody></table></div>
      {current&&<div className="history-details"><h3>Fixture verdicts — {current.run.model}</h3><ul>{current.run.report.rows.map(row=><li key={row.example_id}>{row.example_id}: authored {row.expected}, model {row.model_verdict??"abstained"}</li>)}</ul></div>}</section>
    </>}
    <p className="muted">Fictional authored-label agreement is not independent clinical accuracy. Do not enter patient data or use these metrics for clinical decisions. Imported checksums are not cryptographically verified in this browser view.</p>
  </main>;
}
