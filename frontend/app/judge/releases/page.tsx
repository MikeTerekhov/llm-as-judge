"use client";
import {useEffect,useState} from "react";
type Release={release_id:string;commit_sha:string;recorded_at:string;manifest_sha256:string;report_sha256:string;quality_status:string;readiness_status:string;decision:string;blockers:string[]};
type Registry={count:number;releases:Release[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function ReleasesPage(){
  const [data,setData]=useState<Registry|null>(null);
  const [error,setError]=useState("");
  const [filter,setFilter]=useState("all");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/release-registry",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Registry>})
      .then(setData).catch(e=>{if(e.name!=="AbortError")setError("Release registry disabled or unavailable. Enable only for local operator use.");});
    return ()=>controller.abort();
  },[]);
  const releases=(data?.releases||[]).filter(r=>filter==="all"||r.decision===filter);
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Research release registry</h1>
    <p><a href="/judge">Back to judge evaluation</a></p>
    <p className="muted">Local synthetic research manifests. Decisions are self-asserted, not authenticated approval.</p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!data&&<p role="status">Loading research registry…</p>}
    {data&&<>
      <div className="notice">{data.disclaimer}</div>
      <section className="panel">
        <h2>Release records ({data.count})</h2>
        <label htmlFor="decision">Decision: </label>
        <select id="decision" value={filter} onChange={e=>setFilter(e.target.value)}>
          <option value="all">All</option><option value="pending">Pending</option>
          <option value="approved">Approved</option><option value="rejected">Rejected</option>
        </select>
        {releases.length===0?<p>No matching release records.</p>:releases.map(item=>
          <article className="evidence" key={item.release_id}>
            <h3>{item.release_id}</h3>
            <p>Decision: {item.decision} · Readiness: {item.readiness_status} · Quality: {item.quality_status}</p>
            <p>Commit: <code>{item.commit_sha.slice(0,12)}</code> · Recorded: {item.recorded_at}</p>
            {item.blockers.length>0&&<p>Blockers: {item.blockers.join(", ")}</p>}
            <p className="muted">Manifest checksum: {item.manifest_sha256.slice(0,16)}…</p>
          </article>)}
      </section>
    </>}
  </main>;
}
