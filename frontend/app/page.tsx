"use client";
import { useState } from "react";

type Review = {case_id:string;ready_for_evidence_review:boolean;missing_fields:string[];warnings:string[];disclaimer:string};
type EvidenceHit = {document_id:string;title:string;url:string;version:string;published_on:string;retrieved_at:string;sha256_digest:string;excerpt:string;score:number};
type Assessment = {status:string;claims:unknown[];evidence:EvidenceHit[];warnings:string[];disclaimer:string};
const initial = {case_id:"SYN-001",synthetic:true,hiv_rna_copies_ml:"42000",cd4_cells_mm3:"385",egfr_ml_min_173m2:"78",hbv_status:"unknown",resistance_history:"",current_medications:""};
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function Home(){
  const [form,setForm]=useState(initial);
  const [review,setReview]=useState<Review|null>(null);
  const [assessment,setAssessment]=useState<Assessment|null>(null);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const set=(key:keyof typeof initial,value:string)=>setForm(prev=>({...prev,[key]:value}));
  async function submit(){
    setBusy(true);setError("");setReview(null);setAssessment(null);
    const payload={...form,hiv_rna_copies_ml:form.hiv_rna_copies_ml===""?null:Number(form.hiv_rna_copies_ml),
      cd4_cells_mm3:form.cd4_cells_mm3===""?null:Number(form.cd4_cells_mm3),
      egfr_ml_min_173m2:form.egfr_ml_min_173m2===""?null:Number(form.egfr_ml_min_173m2),
      resistance_history:form.resistance_history||null,
      current_medications:form.current_medications.split(",").map(s=>s.trim()).filter(Boolean)};
    try{
      const responses=await Promise.all(["review","assess"].map(action=>fetch(API+"/api/v1/cases/"+action,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})));
      if(responses.some(r=>!r.ok))throw new Error("API validation failed. Check inputs and backend availability.");
      setReview(await responses[0].json());setAssessment(await responses[1].json());
    }catch(e){setError(e instanceof Error?e.message:"Request failed");}finally{setBusy(false);}
  }
  return <main><p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p><h1>Clinical evidence review</h1><p><a href="/demo">▶ Launch interactive demo (no backend required) →</a></p><p><a href="/judge">View synthetic judge evaluation →</a></p>
    <p className="muted">Synthetic case demonstration. No diagnosis, prescribing, or clinical decisions.</p>
    <div className="notice">Research prototype only. Never enter real patient information, including identifiers or clinical records. A synthetic flag does not detect PHI.</div>
    <section className="panel"><h2>Synthetic case inputs</h2><div className="grid">
      <label>Case ID<input value={form.case_id} onChange={e=>set("case_id",e.target.value)}/></label>
      <label>HIV RNA (copies/mL)<input type="number" min="0" value={form.hiv_rna_copies_ml} onChange={e=>set("hiv_rna_copies_ml",e.target.value)}/></label>
      <label>CD4 (cells/mm³)<input type="number" min="0" value={form.cd4_cells_mm3} onChange={e=>set("cd4_cells_mm3",e.target.value)}/></label>
      <label>eGFR (mL/min/1.73m²)<input type="number" min="0" value={form.egfr_ml_min_173m2} onChange={e=>set("egfr_ml_min_173m2",e.target.value)}/></label>
      <label>HBV status<select value={form.hbv_status} onChange={e=>set("hbv_status",e.target.value)}><option value="unknown">Unknown</option><option value="positive">Positive</option><option value="negative">Negative</option></select></label>
      <label>Resistance history (synthetic)<input value={form.resistance_history} onChange={e=>set("resistance_history",e.target.value)} placeholder="Unknown / fictional history"/></label>
      <label>Medications (comma-separated, fictional)<input value={form.current_medications} onChange={e=>set("current_medications",e.target.value)}/></label>
    </div><p><button disabled={busy} onClick={submit}>{busy?"Reviewing…":"Review synthetic case"}</button></p></section>
    {error&&<div className="notice" role="alert">{error}</div>}
    {review&&assessment&&<section className="panel" aria-live="polite"><h2>Review results</h2>
      <p className="status">Assessment status: {assessment.status.replaceAll("_"," ")}</p>
      <p>Input completeness: {review.ready_for_evidence_review?"Demo fields populated":"Additional information required"}</p>
      <h3>Missing information</h3>{review.missing_fields.length?<ul>{review.missing_fields.map(s=><li key={s}>{s.replaceAll("_"," ")}</li>)}</ul>:<p>None in the demo schema.</p>}
      <h3>Warnings</h3><ul>{[...review.warnings,...assessment.warnings].map((s,i)=><li key={i}>{s}</li>)}</ul>
      <h3>Reviewed evidence snapshots</h3>
      {assessment.evidence.length===0?<p>No matching reviewed evidence. The system abstains from recommendations.</p>:
        <div>{assessment.evidence.map(hit=><article className="evidence" key={hit.document_id}>
          <h4>{hit.title}</h4>
          <p className="muted">Version: {hit.version} · Published: {hit.published_on} · Retrieved: {hit.retrieved_at.slice(0,10)}</p>
          <p>{hit.excerpt}</p>
          <p className="muted">Document ID: {hit.document_id} · SHA-256: <code>{hit.sha256_digest}</code></p>
          <a href={hit.url} target="_blank" rel="noopener noreferrer">Open source page</a>
        </article>)}</div>}
      <p className="muted">Review flags are operator attestations, not proof of source authenticity or medical correctness.</p>
      <p className="muted">{assessment.disclaimer}</p></section>}
  </main>;
}
