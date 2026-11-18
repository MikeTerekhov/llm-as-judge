"use client";
import {useEffect,useState} from "react";
type Row={example_id:string;category:string;reviewers:number;consensus:string|null;disputed:boolean;needs_second_review:boolean};
type Report={total_examples:number;reviewed_examples:number;multiply_reviewed:number;unanimous_count:number;unanimity_rate:number|null;rows:Row[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function AdjudicationPage(){
  const [report,setReport]=useState<Report|null>(null);
  const [error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/adjudication",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Report>})
      .then(setReport).catch(e=>{if(e.name!=="AbortError")setError("Review summary is disabled or unavailable. Operator setup is required.");});
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
