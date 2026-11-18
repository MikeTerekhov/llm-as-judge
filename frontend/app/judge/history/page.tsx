"use client";
import {useEffect,useState} from "react";
type Trend={run_id:string;recorded_at:string;model:string;total:number;model_returned:number;disagreement_count:number;disagreement_rate:number|null};
type Model={model:string;runs:number;judgments:number;disagreements:number;weighted_disagreement_rate:number|null};
type Report={runs:number;trends:Trend[];models:Model[];disclaimer:string};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
function percent(value:number|null){return value===null?"N/A":(value*100).toFixed(1)+"%";}
export default function HistoryPage(){
  const [data,setData]=useState<Report|null>(null);
  const [error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();
    fetch(API+"/api/v1/judge/experiments",{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error("History unavailable or disabled");return r.json() as Promise<Report>})
      .then(setData).catch(e=>{if(e.name!=="AbortError")setError("History is disabled or unavailable. Ask an operator to enable the local history API.");});
    return ()=>controller.abort();
  },[]);
  return <main>
    <p className="muted">AI REGIMEN / RESEARCH WORKSPACE</p>
    <h1>Experiment history</h1>
    <p className="muted">Local synthetic benchmark metadata only. No clinical accuracy claims.</p>
    <p><a href="/judge">Back to judge evaluation</a></p>
    {error&&<div className="notice" role="alert">{error}</div>}
    {!error&&!data&&<p role="status">Loading experiment history…</p>}
    {data&&<>
      <div className="notice">{data.disclaimer}</div>
      <section className="panel"><h2>Experiment trends</h2>
        <p>Total recorded runs: {data.runs}</p>
        {data.trends.length===0?<p>No experiments recorded yet.</p>:
          <div>{data.trends.map(run=><article className="evidence" key={run.run_id}>
            <h3>{run.run_id}</h3>
            <p className="muted">{run.recorded_at} · {run.model}</p>
            <p>Disagreement: {percent(run.disagreement_rate)} · Model judgments: {run.model_returned}/{run.total}</p>
            <div role="img" aria-label={`Disagreement rate ${percent(run.disagreement_rate)}`}
                 style={{height:12,background:"#d1d5db",borderRadius:6,overflow:"hidden"}}>
              <div style={{height:"100%",width:`${(run.disagreement_rate??0)*100}%`,background:"#2563eb"}}/>
            </div>
          </article>)}</div>}
      </section>
      <section className="panel"><h2>Models compared</h2>
        {data.models.length===0?<p>No model results available.</p>:
          <ul>{data.models.map(model=><li key={model.model}>{model.model}: {model.runs} runs, {model.judgments} judgments, weighted disagreement {percent(model.weighted_disagreement_rate)}</li>)}</ul>}
      </section>
    </>}
  </main>;
}
