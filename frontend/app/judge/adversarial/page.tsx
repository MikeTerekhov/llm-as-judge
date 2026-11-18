"use client";
import {useEffect,useState} from "react";
type Example={id:string;category:string;expected_semantic_label:string;lexical_status:string;lexical_coverage:number;potential_false_assurance:boolean;explanation:string};
type ModelReport={total:number;model_returned:number;model_abstained:number;label_agreement_rate:number|null;lexical_disagreement_rate:number|null;categories:Record<string,{examples:number;model_returned:number;matches:number;disagreements:number;label_agreement_rate:number|null;lexical_disagreement_rate:number|null}>};
type Report={total:number;flagged_by_lexical_screen:number;potential_false_assurance_count:number;examples:Example[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function AdversarialPage(){
  const [report,setReport]=useState<Report|null>(null);
  const [error,setError]=useState("");
  const [modelReport,setModelReport]=useState<ModelReport|null>(null);
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/adversarial",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Report>})
      .then(setReport).catch(e=>{if(e.name!=="AbortError")setError("Adversarial benchmark unavailable.");});
    fetch(API+"/api/v1/judge/adversarial-model",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Model report unavailable");return r.json() as Promise<ModelReport>})
      .then(setModelReport).catch(()=>{});
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
      {modelReport&&<section className="panel"><h2>LLM benchmark status</h2>
        <p>Model verdicts: {modelReport.model_returned}/{modelReport.total} · Abstentions: {modelReport.model_abstained}</p>
        <p>Fixture-label agreement: {modelReport.label_agreement_rate===null?"N/A — model not run":(modelReport.label_agreement_rate*100).toFixed(1)+"%"}</p>
        <p>Lexical/model disagreement: {modelReport.lexical_disagreement_rate===null?"N/A — model not run":(modelReport.lexical_disagreement_rate*100).toFixed(1)+"%"}</p>
        <ul>{Object.entries(modelReport.categories).map(([name,item])=><li key={name}>{name}: {item.model_returned}/{item.examples} model verdicts; label agreement {item.label_agreement_rate===null?"N/A":(item.label_agreement_rate*100).toFixed(1)+"%"}</li>)}</ul>
        <p className="muted">Hand-authored fictional labels, not independently validated clinical truth.</p>
      </section>}
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
