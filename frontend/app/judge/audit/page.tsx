"use client";
import {useEffect,useState} from "react";
type Event={sequence:number;event_type:string;release_id:string;artifact_sha256:string;actor_id:string|null;recorded_at:string;previous_sha256:string|null;event_sha256:string};
type Audit={total_events:number;matched_events:number;chain_head_sha256:string|null;events:Event[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export default function AuditPage(){
  const [data,setData]=useState<Audit|null>(null);
  const [error,setError]=useState("");
  const [filter,setFilter]=useState("");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/audit-trail",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("Unavailable");return r.json() as Promise<Audit>})
      .then(setData).catch(e=>{if(e.name!=="AbortError")setError("Audit trail is disabled or unavailable. Enable for local operator use only.");});
    return ()=>controller.abort();
  },[]);
  const events=(data?.events||[]).filter(e=>e.release_id.toLowerCase().includes(filter.toLowerCase()));
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Research audit trail</h1>
    <p><a href="/judge/releases">Back to release registry</a></p>
    <p className="muted">Local checksum-chained events. Actor identities are not authenticated.</p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!data&&<p role="status">Loading audit trail…</p>}
    {data&&<>
      <div className="notice">{data.disclaimer}</div>
      <section className="panel">
        <h2>Events ({data.total_events})</h2>
        <p>Chain head: <code>{data.chain_head_sha256?.slice(0,20)??"No events"}…</code></p>
        <label htmlFor="release-filter">Filter release: </label>
        <input id="release-filter" value={filter} onChange={e=>setFilter(e.target.value)}/>
        {events.length===0?<p>No matching events.</p>:events.map(item=>
          <article className="evidence" key={item.sequence}>
            <h3>#{item.sequence} · {item.event_type.replaceAll("_"," ")}</h3>
            <p>Release: {item.release_id} · {item.recorded_at}</p>
            <p>Actor: {item.actor_id??"unspecified"} · Artifact: <code>{item.artifact_sha256.slice(0,16)}…</code></p>
            <p className="muted">Event checksum: {item.event_sha256.slice(0,20)}…</p>
          </article>)}
      </section>
    </>}
  </main>;
}
