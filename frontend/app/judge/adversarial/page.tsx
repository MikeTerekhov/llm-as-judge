"use client";
import {useEffect,useState} from "react";
type Example={id:string;category:string;expected_semantic_label:string;lexical_status:string;lexical_coverage:number;potential_false_assurance:boolean;explanation:string};
type Classification={total:number;evaluated:number;abstained:number;coverage:number|null;accuracy:number|null;macro_f1:number|null;confusion:Record<string,Record<string,number>>;per_label:Record<string,{support:number;predicted:number;precision:number|null;recall:number|null;f1:number|null}>};
type ModelReport={classification:Classification;total:number;model_returned:number;model_abstained:number;label_agreement_rate:number|null;lexical_disagreement_rate:number|null;categories:Record<string,{examples:number;model_returned:number;matches:number;disagreements:number;label_agreement_rate:number|null;lexical_disagreement_rate:number|null}>};
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
    <h1>Adversarial evaluation</h1><p><a href="/judge/adjudication">View human review status →</a></p>
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
        {modelReport.classification&&<div><h3>Semantic classification metrics</h3><p>Verdict coverage: {(modelReport.classification.coverage===null?"N/A":(modelReport.classification.coverage*100).toFixed(1)+"%")} · Agreement accuracy: {modelReport.classification.accuracy===null?"N/A — model not run":(modelReport.classification.accuracy*100).toFixed(1)+"%"} · Macro F1: {modelReport.classification.macro_f1===null?"N/A":modelReport.classification.macro_f1.toFixed(3)}</p><h4>Per-label precision, recall and F1</h4><ul>{Object.entries(modelReport.classification.per_label).map(([label,metric])=><li key={label}>{label}: precision {metric.precision===null?"N/A":metric.precision.toFixed(3)}, recall {metric.recall===null?"N/A":metric.recall.toFixed(3)}, F1 {metric.f1===null?"N/A":metric.f1.toFixed(3)} (support {metric.support})</li>)}</ul><h4>Confusion counts (authored label → model verdict)</h4><ul>{Object.entries(modelReport.classification.confusion).flatMap(([expected,predictions])=>Object.entries(predictions).map(([predicted,count])=><li key={expected+predicted}>{expected} → {predicted}: {count}</li>))}</ul></div>}
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
