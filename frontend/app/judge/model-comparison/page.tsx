"use client";
import {useState} from "react";
import Link from "next/link";
import "./comparison.css";

const LABELS=["supported","contradicted","insufficient_evidence"] as const;
type Label=typeof LABELS[number];
type Row={example_id:string;expected:Label;model_verdict:Label|null};
type Report={mode:string;model:string;report:{total:number;rows:Row[]}};
type Summary={model:string;coverage:number;accuracy:number|null;macroF1:number|null;returned:number;rows:Map<string,Row>};
type Pair={left:number;right:number;shared:number;disagreements:number;rate:number|null;leftAgreement:number|null;rightAgreement:number|null};
const pct=(n:number|null)=>n===null?"N/A":(n*100).toFixed(1)+"%";
function parseReport(raw:unknown):Report{
  if(!raw||typeof raw!=="object")throw Error("Expected a JSON report object.");
  const r=raw as Partial<Report>;
  if(r.mode!=="executed"||typeof r.model!=="string"||!r.model.trim()||!r.report||!Array.isArray(r.report.rows)||r.report.total!==12||r.report.rows.length!==12)throw Error("Expected an executed AR-039 report with 12 fictional fixtures.");
  const ids=new Set<string>();
  for(const row of r.report.rows){
    if(!row||typeof row.example_id!=="string"||!row.example_id||ids.has(row.example_id)||!LABELS.includes(row.expected)||!(row.model_verdict===null||LABELS.includes(row.model_verdict)))throw Error("Invalid or duplicate fixture ID, label, or verdict.");
    ids.add(row.example_id);
  }
  return r as Report;
}
function summarize(report:Report):Summary{
  const rows=new Map(report.report.rows.map(r=>[r.example_id,r]));
  const evaluated=report.report.rows.filter(r=>r.model_verdict!==null);
  const accuracy=evaluated.length?evaluated.filter(r=>r.expected===r.model_verdict).length/evaluated.length:null;
  const f1s=LABELS.map(label=>{
    const tp=evaluated.filter(r=>r.expected===label&&r.model_verdict===label).length;
    const predicted=evaluated.filter(r=>r.model_verdict===label).length;
    const actual=evaluated.filter(r=>r.expected===label).length;
    const precision=predicted?tp/predicted:null;
    const recall=actual?tp/actual:null;
    return precision!==null&&recall!==null&&precision+recall>0?2*precision*recall/(precision+recall):null;
  }).filter((n):n is number=>n!==null);
  return {model:report.model,coverage:evaluated.length/12,accuracy,macroF1:f1s.length?f1s.reduce((a,b)=>a+b,0)/f1s.length:null,returned:evaluated.length,rows};
}
function compare(reports:Report[]):{summaries:Summary[];pairs:Pair[]}{
  if(reports.length<2)throw Error("Upload at least two executed model reports.");
  const first=new Map(reports[0].report.rows.map(r=>[r.example_id,r.expected]));
  for(const report of reports.slice(1)){
    const rows=new Map(report.report.rows.map(r=>[r.example_id,r.expected]));
    if(first.size!==rows.size||[...first].some(([id,label])=>rows.get(id)!==label))throw Error("Fixture IDs or authored labels differ between reports.");
  }
  const summaries=reports.map(summarize);
  const pairs:Pair[]=[];
  for(let i=0;i<summaries.length;i++)for(let j=i+1;j<summaries.length;j++){
    const a=summaries[i].rows,b=summaries[j].rows;
    const shared=[...a.keys()].filter(id=>a.get(id)?.model_verdict!==null&&b.get(id)?.model_verdict!==null);
    const disagreements=shared.filter(id=>a.get(id)?.model_verdict!==b.get(id)?.model_verdict).length;
    const correct=(rows:Map<string,Row>)=>shared.filter(id=>rows.get(id)?.model_verdict===first.get(id)).length;
    pairs.push({left:i,right:j,shared:shared.length,disagreements,rate:shared.length?disagreements/shared.length:null,leftAgreement:shared.length?correct(a)/shared.length:null,rightAgreement:shared.length?correct(b)/shared.length:null});
  }
  return {summaries,pairs};
}
export default function ModelComparisonPage(){
  const [reports,setReports]=useState<Report[]>([]);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [selection,setSelection]=useState<[number,number]>([0,1]);
  async function load(files:FileList|null){
    if(!files)return;
    setBusy(true);setError("");
    try{
      if(files.length<2||files.length>8)throw Error("Choose between 2 and 8 JSON reports.");
      const loaded:Report[]=[];
      for(const file of Array.from(files)){
        if(file.size>1024*1024)throw Error("Each report must be 1 MiB or smaller.");
        loaded.push(parseReport(JSON.parse(await file.text())));
      }
      compare(loaded);
      setReports(loaded);setSelection([0,1]);
    }catch(e){setReports([]);setError(e instanceof Error?e.message:"Could not read JSON reports.");}
    finally{setBusy(false);}
  }
  const result=reports.length>=2?compare(reports):null;
  const left=result?.summaries[selection[0]],right=result?.summaries[selection[1]];
  const disagreements=left&&right?[...left.rows.keys()].filter(id=>left.rows.get(id)?.model_verdict!==null&&right.rows.get(id)?.model_verdict!==null&&left.rows.get(id)?.model_verdict!==right.rows.get(id)?.model_verdict):[];
  return <main className="model-compare">
    <p className="muted">AI REGIMEN / SYNTHETIC RESEARCH</p>
    <h1>Compare LLM evaluation runs</h1>
    <p>Upload 2–8 executed AR-039 JSON reports to compare model verdict coverage, authored-label agreement and disagreements on identical fictional test cases. Analysis happens locally in your browser; files are not uploaded to the API.</p>
    <p><Link href="/judge/overview">Research overview</Link> · <Link href="/judge/adversarial">Adversarial benchmark</Link></p>
    <section className="panel"><h2>Load benchmark reports</h2>
      <label htmlFor="model-reports">Select JSON reports (maximum 1 MiB each)</label>
      <input id="model-reports" type="file" accept=".json,application/json" multiple onChange={e=>void load(e.target.files)} disabled={busy}/>
      {busy&&<p role="status">Reading local reports…</p>}
      {error&&<p role="alert" className="notice">{error}</p>}
      <p className="muted">Dry-run reports and mismatched fixtures are rejected. Model names come from supplied files and are not independently authenticated.</p>
    </section>
    {result&&<>
      <section className="panel"><h2>Model metrics</h2><div className="compare-grid">{result.summaries.map((item,i)=><article className="compare-card" key={i}><h3>{item.model} <small>Run {i+1}</small></h3><p>Returned: {item.returned}/12 · Coverage: {pct(item.coverage)}</p><p>Conditional label agreement: {pct(item.accuracy)}</p><p>Macro F1: {item.macroF1===null?"N/A":item.macroF1.toFixed(3)}</p><div className="compare-track" aria-label={`Verdict coverage ${pct(item.coverage)}`}><div style={{width:pct(item.coverage)}}/></div></article>)}</div></section>
      <section className="panel"><h2>Paired comparisons</h2><div className="compare-scroll"><table><thead><tr><th>Models</th><th>Shared verdicts</th><th>Disagreement</th><th>Left agreement</th><th>Right agreement</th></tr></thead><tbody>{result.pairs.map(pair=><tr key={pair.left+"-"+pair.right}><td>{pair.left+1} vs {pair.right+1}</td><td>{pair.shared}/12</td><td>{pct(pair.rate)}</td><td>{pct(pair.leftAgreement)}</td><td>{pct(pair.rightAgreement)}</td></tr>)}</tbody></table></div><p className="muted">Pairwise rates use only fixtures for which both models returned verdicts. No shared verdicts means N/A.</p></section>
      <section className="panel"><h2>Inspect disagreements</h2><div className="compare-selects"><label>First run <select value={selection[0]} onChange={e=>setSelection([Number(e.target.value),selection[1]])}>{result.summaries.map((s,i)=><option key={i} value={i}>{i+1}: {s.model}</option>)}</select></label><label>Second run <select value={selection[1]} onChange={e=>setSelection([selection[0],Number(e.target.value)])}>{result.summaries.map((s,i)=><option key={i} value={i}>{i+1}: {s.model}</option>)}</select></label></div>{selection[0]===selection[1]?<p>Choose two different runs.</p>:disagreements.length?<ul>{disagreements.map(id=><li key={id}><strong>{id}</strong>: authored {left?.rows.get(id)?.expected}; {left?.model} → {left?.rows.get(id)?.model_verdict}; {right?.model} → {right?.rows.get(id)?.model_verdict}</li>)}</ul>:<p>No disagreements among shared returned verdicts.</p>}</section>
    </>}
    <p className="muted">Research prototype only. Agreement with hand-authored fictional labels is not clinical accuracy. No patient information or treatment decisions.</p>
  </main>;
}
