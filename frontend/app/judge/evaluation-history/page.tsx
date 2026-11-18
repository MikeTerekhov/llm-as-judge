"use client";
import {useEffect,useState} from "react";
type Snapshot={snapshot:string;report_sha256:string;dataset_sha256:string;fixture_count:number;review_count:number;quality_status:string;regression_status:string|null;regression_blockers:string[];changed_examples:number;review_counts_changed:boolean};
type History={snapshots:Snapshot[];count:number;disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function EvaluationHistoryPage(){
  const [data,setData]=useState<History|null>(null);
  const [error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/evaluation-history",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("History unavailable");return r.json() as Promise<History>})
      .then(setData).catch(e=>{if(e.name!=="AbortError")setError("Evaluation history is disabled or unavailable. Enable it locally as an operator.");});
    return ()=>controller.abort();
  },[]);
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Evaluation history</h1>
    <p><a href="/judge">Back to judge evaluation</a></p>
    <p className="muted">Checksum-verified synthetic report snapshots, not clinical validation.</p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!data&&<p role="status">Loading evaluation snapshots…</p>}
    {data&&<>
      <div className="notice">{data.disclaimer}</div>
      <section className="panel"><h2>Snapshot timeline</h2>
        <p>Verified reports: {data.count}</p>
        {data.snapshots.length===0?<p>No snapshots saved yet.</p>:data.snapshots.map(item=>
          <article className="evidence" key={item.snapshot}>
            <h3>{item.snapshot}</h3>
            <p>Fixtures: {item.fixture_count} · Reviews: {item.review_count} · Review quality: {item.quality_status}</p>
            <p>Regression: {item.regression_status??"Baseline"} · Changed cases: {item.changed_examples}</p>
            {item.regression_blockers.length>0&&<p>Flags: {item.regression_blockers.join(", ")}</p>}
            {item.review_counts_changed&&<p>Review label counts changed</p>}
            <p className="muted">Report checksum: <code>{item.report_sha256.slice(0,16)}…</code></p>
          </article>)}
      </section>
    </>}
  </main>;
}
