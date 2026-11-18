"use client";
import {useEffect,useState} from "react";
type Example={id:string;category:string;claim:string;expected:string;predicted:string;lexical_coverage:number;missing_terms:string[];reasons:string[]};
type Report={summary:{total:number;correct:number;accuracy:number;confusion:Record<string,Record<string,number>>;per_category:Record<string,{count:number;accuracy:number}>};examples:Example[];model_enabled:boolean;disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function JudgePage(){
  const [report,setReport]=useState<Report|null>(null);
  const [error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/benchmark",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Benchmark API unavailable");return r.json() as Promise<Report>})
      .then(setReport).catch(e=>{if(e.name!=="AbortError")setError("Could not load synthetic benchmark.");});
    return ()=>controller.abort();
  },[]);
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Judge evaluation</h1>
    <p className="muted">Read-only synthetic benchmark. No external LLM calls or clinical validation.</p>
    <p><a href="/">Back to case review</a></p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!report&&<p role="status">Loading benchmark…</p>}
    {report&&<>
      <div className="notice">{report.disclaimer}</div>
      <section className="panel"><h2>Baseline metrics</h2>
        <p>Examples: {report.summary.total} · Matched expected labels: {report.summary.correct} · Fixture accuracy: {(report.summary.accuracy*100).toFixed(1)}%</p>
        <p className="muted">These expected labels were written for the deterministic screener. This is not an independent accuracy estimate.</p>
        <h3>Categories</h3>
        <ul>{Object.entries(report.summary.per_category).map(([name,metric])=><li key={name}>{name.replaceAll("_"," ")}: {metric.count} example(s), {(metric.accuracy*100).toFixed(0)}% fixture agreement</li>)}</ul>
        <h3>Confusion counts</h3>
        <ul>{Object.entries(report.summary.confusion).flatMap(([expected,predictions])=>Object.entries(predictions).map(([predicted,count])=><li key={expected+predicted}>Expected {expected}, predicted {predicted}: {count}</li>))}</ul>
      </section>
      <section className="panel"><h2>Claim-level explanations</h2>
        {report.examples.map(item=><article className="evidence" key={item.id}>
          <h3>{item.category.replaceAll("_"," ")}</h3>
          <p>Claim: {item.claim||"(empty)"}</p>
          <p>Expected: {item.expected} · Predicted: {item.predicted} · Token coverage: {(item.lexical_coverage*100).toFixed(0)}%</p>
          {item.missing_terms.length>0&&<p>Missing terms: {item.missing_terms.join(", ")}</p>}
          <ul>{item.reasons.map((reason,i)=><li key={i}>{reason}</li>)}</ul>
        </article>)}
      </section>
    </>}
  </main>;
}
