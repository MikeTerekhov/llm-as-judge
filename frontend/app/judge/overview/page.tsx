"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import "./dashboard.css";

type Adversarial={total:number;flagged_by_lexical_screen:number;potential_false_assurance_count:number;disclaimer:string};
type Model={total:number;model_returned:number;model_abstained:number;disclaimer:string};
type Human={total_examples:number;reviewed_examples:number;multiply_reviewed:number;unanimity_rate:number|null;disclaimer:string};
type Gates={status:string;checks:{name:string;passed:boolean;observed:number|null;threshold:number}[];disclaimer:string};
type State<T>={status:"loading"|"ready"|"unavailable";data:T|null};
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
const empty=<T,>():State<T>=>({status:"loading",data:null});
async function request<T>(path:string,signal:AbortSignal):Promise<State<T>>{
  try{
    const response=await fetch(API+path,{signal,cache:"no-store"});
    if(!response.ok)return {status:"unavailable",data:null};
    return {status:"ready",data:await response.json() as T};
  }catch{return {status:"unavailable",data:null};}
}
function Metric({label,value,detail}:{label:string;value:string;detail:string}){
  return <article className="research-metric"><p>{label}</p><strong>{value}</strong><small>{detail}</small></article>;
}
export default function ResearchDashboard(){
  const [lexical,setLexical]=useState<State<Adversarial>>(empty);
  const [model,setModel]=useState<State<Model>>(empty);
  const [human,setHuman]=useState<State<Human>>(empty);
  const [gates,setGates]=useState<State<Gates>>(empty);
  const [refresh,setRefresh]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),7000);
    void Promise.all([
      request<Adversarial>("/api/v1/judge/adversarial",controller.signal).then(setLexical),
      request<Model>("/api/v1/judge/adversarial-model",controller.signal).then(setModel),
      request<Human>("/api/v1/judge/adjudication",controller.signal).then(setHuman),
      request<Gates>("/api/v1/judge/quality-gates",controller.signal).then(setGates)
    ]).finally(()=>clearTimeout(timer));
    return ()=>{controller.abort();clearTimeout(timer);};
  },[refresh]);
  const state=(value:State<unknown>)=>value.status==="ready"?"Available":value.status==="loading"?"Loading":"Unavailable / disabled";
  return <main className="research-dashboard">
    <p className="muted">AI REGIMEN / SYNTHETIC RESEARCH</p>
    <h1>Research evaluation overview</h1>
    <p>One read-only view of deterministic screening, model availability, human annotation and process quality gates. All cases are fictional. Nothing here establishes clinical correctness.</p>
    <div className="research-actions"><button onClick={()=>{setLexical(empty());setModel(empty());setHuman(empty());setGates(empty());setRefresh(v=>v+1);}}>Refresh research status</button><Link href="/demo">Guided demo</Link><Link href="/judge">Detailed evaluations</Link><Link href="/judge/model-comparison">Compare model runs</Link><Link href="/judge/experiment-history">Experiment history</Link></div>
    <div className="research-metrics">
      <Metric label="Fictional stress tests" value={lexical.data?String(lexical.data.total):"—"} detail={state(lexical)}/>
      <Metric label="Lexical false-assurance risks" value={lexical.data?String(lexical.data.potential_false_assurance_count):"—"} detail="Flagged for human attention, not validated errors"/>
      <Metric label="Model verdicts returned" value={model.data?`${model.data.model_returned} / ${model.data.total}`:"—"} detail={model.data?"No model executed by dashboard":state(model)}/>
      <Metric label="Human reviewed cases" value={human.data?`${human.data.reviewed_examples} / ${human.data.total_examples}`:"—"} detail={state(human)}/>
    </div>
    <div className="research-columns">
      <section className="panel"><h2>Deterministic lexical screening</h2><p role="status">{state(lexical)}</p>{lexical.data&&<><p>{lexical.data.flagged_by_lexical_screen} / {lexical.data.total} cases flagged by lexical screening.</p><p>{lexical.data.disclaimer}</p></>}<Link href="/judge/adversarial">Inspect adversarial cases</Link></section>
      <section className="panel"><h2>Optional model evaluation</h2><p role="status">{state(model)}</p>{model.data&&<><p>{model.data.model_returned} verdicts, {model.data.model_abstained} abstentions or not-run outcomes.</p><p>{model.data.disclaimer}</p></>}<p className="muted">The dashboard does not call an LLM or treat missing verdicts as zero accuracy.</p></section>
      <section className="panel"><h2>Human adjudication</h2><p role="status">{state(human)}</p>{human.data&&<><p>{human.data.multiply_reviewed} cases have at least two reviewers. Unanimity: {human.data.unanimity_rate===null?"Not measurable":(human.data.unanimity_rate*100).toFixed(1)+"%"}.</p><p>{human.data.disclaimer}</p></>}<p className="muted">Disabled unless the local review API is explicitly enabled.</p></section>
      <section className="panel"><h2>Research quality gates</h2><p role="status">{state(gates)}</p>{gates.data&&<><p className="research-gate-status">Process gate status: {gates.data.status}</p><ul>{gates.data.checks.map(check=><li key={check.name}>{check.passed?"Pass":"Blocked"} · {check.name.replaceAll("_"," ")} · observed {check.observed===null?"N/A":check.observed}, threshold {check.threshold}</li>)}</ul><p>{gates.data.disclaimer}</p></>}<p className="muted">Unavailable is not a pass. Process gates are not clinical validation.</p></section>
    </div>
    <p className="research-disclaimer">Research prototype only. Do not enter patient information. No diagnosis, treatment recommendations or prescribing.</p>
  </main>;
}
