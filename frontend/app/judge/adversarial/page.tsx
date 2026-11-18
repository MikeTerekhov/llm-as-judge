"use client";
import {useEffect,useState} from "react";
type Example={id:string;category:string;expected_semantic_label:string;lexical_status:string;lexical_coverage:number;potential_false_assurance:boolean;explanation:string};
type Report={total:number;flagged_by_lexical_screen:number;potential_false_assurance_count:number;examples:Example[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function AdversarialPage(){
  const [report,setReport]=useState<Report|null>(null);
  const [error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/adversarial",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Report>})
      .then(setReport).catch(e=>{if(e.name!=="AbortError")setError("Adversarial benchmark unavailable.");});
    return ()=>controller.abort();
  },[]);
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Adversarial evaluation</h1>
    <p><a href="/judge">Back to judge evaluation</a></p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!report&&<p role="status">Loading synthetic cases…</p>}
    {report&&<>
      <div className="notice">{report.disclaimer}</div>
      <section className="panel"><h2>Stress-test overview</h2>
        <p>Fictional cases: {report.total} · Lexical flags: {report.flagged_by_lexical_screen} · Potential false-assurance cases: {report.potential_false_assurance_count}</p>
        <p className="muted">A lexical review-required result is not semantic entailment or clinical approval.</p>
      </section>
      <section className="panel"><h2>Individual cases</h2>
        {report.examples.map(item=><article className="evidence" key={item.id}>
          <h3>{item.id.replaceAll("-"," ")}</h3>
          <p>Category: {item.category} · Hand-authored semantic label: {item.expected_semantic_label}</p>
          <p>Lexical screen: {item.lexical_status} · Coverage: {(item.lexical_coverage*100).toFixed(0)}%</p>
          <p>{item.explanation}</p>
          {item.potential_false_assurance&&<p className="status">Lexical overlap may be misleading; manual review required.</p>}
        </article>)}
      </section>
    </>}
  </main>;
}
