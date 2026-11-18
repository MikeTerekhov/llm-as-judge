"use client";
import {useEffect,useState} from "react";
type Row={example_id:string;category:string;reviewers:number;consensus:string|null;disputed:boolean;needs_second_review:boolean};
type Quality={status:string;checks:{name:string;passed:boolean;observed:number|null;threshold:number}[];disclaimer:string};
type Reliability={reviewer_count:number;pairwise_cohen:{reviewer_a:string;reviewer_b:string;paired_examples:number;kappa:number|null}[];fleiss:{items:number;raters_per_item:number|null;kappa:number|null};categories:Record<string,{reviewed:number;multiply_reviewed:number;disputed:number}>};
type Report={total_examples:number;reviewed_examples:number;multiply_reviewed:number;unanimous_count:number;unanimity_rate:number|null;rows:Row[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function AdjudicationPage(){
  const [report,setReport]=useState<Report|null>(null);
  const [error,setError]=useState("");
  const [reliability,setReliability]=useState<Reliability|null>(null);
  const [quality,setQuality]=useState<Quality|null>(null);
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/adjudication",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Report>})
      .then(setReport).catch(e=>{if(e.name!=="AbortError")setError("Review summary is disabled or unavailable. Operator setup is required.");});
    fetch(API+"/api/v1/judge/reliability",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Reliability>})
      .then(setReliability).catch(()=>{});
    fetch(API+"/api/v1/judge/quality-gates",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Quality>})
      .then(setQuality).catch(()=>{});
    return ()=>controller.abort();
  },[]);
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Human adjudication</h1>
    <p><a href="/judge/adversarial">Back to adversarial evaluation</a></p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!report&&<p role="status">Loading review summary…</p>}
    {report&&<>
      <div className="notice">{report.disclaimer}</div>
      <section className="panel"><h2>Reviewer consistency</h2>
        <p>Reviewed: {report.reviewed_examples}/{report.total_examples} · Multiple reviews: {report.multiply_reviewed}</p>
        <p>Unanimity among multiply-reviewed cases: {report.unanimity_rate===null?"N/A":(report.unanimity_rate*100).toFixed(1)+"%"}</p>
      </section>
      {quality&&<section className="panel"><h2>Benchmark quality gates</h2>
        <p>Review readiness: {quality.status==="pass"?"Passed process checks":"Blocked — further review required"}</p>
        <ul>{quality.checks.map(check=><li key={check.name}>{check.name.replaceAll("_"," ")}: {check.passed?"Pass":"Blocked"} · Observed {check.observed===null?"N/A":check.observed.toFixed(3)} · Threshold {check.threshold.toFixed(3)}</li>)}</ul>
        <p className="muted">{quality.disclaimer}</p>
      </section>}
      {reliability&&<section className="panel"><h2>Inter-rater reliability</h2>
        <p>Reviewers: {reliability.reviewer_count} · Fleiss kappa: {reliability.fleiss.kappa===null?"N/A":reliability.fleiss.kappa.toFixed(3)}</p>
        <h3>Reviewer pairs</h3>
        {reliability.pairwise_cohen.length===0?<p>No overlapping reviewer pairs yet.</p>:<ul>{reliability.pairwise_cohen.map(pair=><li key={pair.reviewer_a+"-"+pair.reviewer_b}>{pair.reviewer_a} / {pair.reviewer_b}: {pair.paired_examples} paired, Cohen kappa {pair.kappa===null?"N/A":pair.kappa.toFixed(3)}</li>)}</ul>}
        <h3>Disputes by category</h3>
        <ul>{Object.entries(reliability.categories).map(([category,counts])=><li key={category}>{category}: {counts.disputed}/{counts.multiply_reviewed} multiply-reviewed cases disputed</li>)}</ul>
        <p className="muted">Kappa measures consistency, not semantic or clinical correctness.</p>
      </section>}
      <section className="panel"><h2>Case review status</h2>
        {report.rows.map(item=><article className="evidence" key={item.example_id}>
          <h3>{item.example_id}</h3>
          <p>{item.category} · {item.reviewers} reviewer(s)</p>
          <p>{item.disputed?"Disputed — further review needed":item.needs_second_review?"Awaiting second review":`Unanimous: ${item.consensus}`}</p>
        </article>)}
      </section>
    </>}
  </main>;
}
