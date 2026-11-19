"use client";
import {useMemo,useState} from "react";
import fixtures from "./demo-fixtures.json";
import "./demo.css";

type Verdict="supported"|"contradicted"|"insufficient_evidence";
type Example=(typeof fixtures)[number];
const steps=["Overview","Evidence challenge","Evaluation","Research governance"];
const verdicts:{value:Verdict;label:string}[]=[
  {value:"supported",label:"Supported"},
  {value:"contradicted",label:"Contradicted"},
  {value:"insufficient_evidence",label:"Insufficient evidence"}
];
const title=(s:string)=>s.replaceAll("_"," ");

export default function DemoPage(){
  const [step,setStep]=useState(0);
  const [index,setIndex]=useState(0);
  const [answers,setAnswers]=useState<Record<string,Verdict>>({});
  const [revealed,setRevealed]=useState<Record<string,boolean>>({});
  const [history,setHistory]=useState(false);
  const [decision,setDecision]=useState<"pending"|"rejected">("pending");
  const example:Example=fixtures[index];
  const answered=Object.keys(answers).length;
  const correct=fixtures.filter(f=>answers[f.id]===f.expected).length;
  const reviewed=fixtures.filter(f=>revealed[f.id]).length;
  const baseline=useMemo(()=>fixtures.map((f,i)=>({id:f.id,expected:f.expected,
    simulated:i===0?"supported":i===1?"supported":f.expected})),[]);
  const mismatches=baseline.filter(r=>r.simulated!==r.expected);
  function exportResults(){
    const results=fixtures.map(f=>({fixture_id:f.id,category:f.category,author_label:f.expected,participant_answer:answers[f.id]??null,explanation_revealed:!!revealed[f.id],matches_author_label:answers[f.id]?answers[f.id]===f.expected:null}));
    const report={schema_version:"1.0",kind:"synthetic_interactive_demo",fixture_count:fixtures.length,answered_count:answered,matching_author_labels:correct,results,limitations:["Fictional author labels are not clinical ground truth.","No live LLM or clinical evaluation was performed.","Research-governance events in the walkthrough are simulated and not persisted."]};
    const blob=new Blob([JSON.stringify(report,null,2)+"\\n"],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const link=document.createElement("a");link.href=url;link.download="ai-regimen-demo-results.json";document.body.appendChild(link);link.click();link.remove();
    URL.revokeObjectURL(url);
  }
  function reset(){setStep(0);setIndex(0);setAnswers({});setRevealed({});setHistory(false);setDecision("pending");}
  return <main className="demo-shell">
    <header className="demo-top">
      <a href="/" className="demo-brand">AI <span>REGIMEN</span></a>
      <div className="demo-top-right"><span className="demo-pill">Offline guided demo</span><a href="/judge">Research workspace ↗</a></div>
    </header>
    <div className="demo-hero">
      <p className="demo-eyebrow">RESEARCH LAB / INTERACTIVE WALKTHROUGH</p>
      <h1>Can an AI tell when evidence <em>doesn’t</em> support a claim?</h1>
      <p>Explore evidence grounding, adversarial evaluation, and research quality gates in four short steps. No setup, API keys, or backend required.</p>
      <div className="demo-hero-meta"><span>06 fictional examples</span><span>04 steps</span><span>Zero patient data</span></div>
    </div>
    <nav className="demo-steps" aria-label="Demo steps">
      {steps.map((name,i)=><button key={name} className={"demo-step "+(i===step?"active":"")} onClick={()=>setStep(i)} aria-current={i===step?"step":undefined}><span>{String(i+1).padStart(2,"0")}</span>{name}</button>)}
    </nav>
    {step===0&&<section className="demo-panel demo-intro">
      <div><p className="demo-eyebrow">01 / THE PROBLEM</p><h2>Similar words can hide different meanings.</h2>
        <p>A claim and a cited passage may share almost every word while making opposite statements. Lexical overlap alone is not a reliable measure of factual support.</p>
        <div className="demo-quote"><span>CLAIM</span><p>The blue beacon is active.</p><span>EVIDENCE</span><p>The blue beacon is <strong>not</strong> active.</p></div>
      </div>
      <aside className="demo-aside"><div className="demo-stat">01 <span>word</span></div><p>One negation changes the meaning of the entire sentence.</p><p className="demo-muted">This is a fictional stress-test example, not a clinical claim.</p></aside>
    </section>}
    {step===1&&<section className="demo-panel">
      <div className="demo-section-heading"><div><p className="demo-eyebrow">02 / EVIDENCE CHALLENGE</p><h2>You be the evaluator.</h2><p>Read the claim and cited evidence. Choose whether the evidence actually supports the claim.</p></div><span className="demo-count">{index+1} / {fixtures.length}</span></div>
      <div className="demo-case-tabs" role="group" aria-label="Choose fictional case">{fixtures.map((f,i)=><button key={f.id} aria-label={"Case "+(i+1)+": "+f.category} aria-pressed={index===i} className={index===i?"selected":""} onClick={()=>setIndex(i)}>{String(i+1).padStart(2,"0")}{revealed[f.id]?" ✓":""}</button>)}</div>
      <div className="demo-case-label">{example.category} / synthetic fixture</div>
      <div className="demo-evidence-grid"><article><span>CLAIM TO CHECK</span><p>{example.claim}</p></article><article><span>CITED EVIDENCE</span><p>{example.evidence}</p></article></div>
      <fieldset className="demo-choices"><legend>Does the cited passage support the claim?</legend>{verdicts.map(v=><label key={v.value} className={answers[example.id]===v.value?"picked":""}><input type="radio" name={"answer-"+example.id} checked={answers[example.id]===v.value} onChange={()=>{setAnswers(a=>({...a,[example.id]:v.value}));setRevealed(r=>({...r,[example.id]:false}));}}/>{v.label}</label>)}</fieldset>
      <button disabled={!answers[example.id]} onClick={()=>setRevealed(r=>({...r,[example.id]:true}))}>Reveal fixture explanation</button>
      {revealed[example.id]&&<div className="demo-feedback" role="status"><p className="demo-eyebrow">{answers[example.id]===example.expected?"MATCHES AUTHOR LABEL":"DIFFERS FROM AUTHOR LABEL"}</p><h3>Expected: {title(example.expected)}</h3><p>{example.explanation}</p><p className="demo-muted">This label was authored for a fictional benchmark; it is not independent clinical ground truth.</p></div>}
      <div className="demo-bottom"><span>{reviewed} / {fixtures.length} explanations revealed</span><button className="demo-secondary" onClick={()=>setIndex((index+1)%fixtures.length)}>Next example →</button></div>
    </section>}
    {step===2&&<section className="demo-panel">
      <p className="demo-eyebrow">03 / EVALUATION</p><h2>Where simple evaluation can go wrong.</h2>
      <p>These illustrative outputs simulate an overly permissive lexical baseline, not the live application's measured predictions. Compare them with the fictional author labels.</p>
      <div className="demo-metrics"><div><strong>{fixtures.length}</strong><span>Illustrative fixtures</span></div><div><strong>{mismatches.length}</strong><span>Illustrative mismatches</span></div><div><strong>{answered}</strong><span>Your answers</span></div><div><strong>{correct}</strong><span>Matching author labels</span></div></div>
      <div className="demo-table-wrap"><table className="demo-table"><thead><tr><th>Fixture</th><th>Author label</th><th>Illustrative lexical result</th><th>Comparison</th></tr></thead><tbody>{baseline.map(r=><tr key={r.id}><td>{title(r.id)}</td><td>{title(r.expected)}</td><td>{title(r.simulated)}</td><td>{r.expected===r.simulated?"Match":"Mismatch"}</td></tr>)}</tbody></table></div>
      <div className="demo-export"><div><h3>Your demo results</h3><p>{answered} of {fixtures.length} cases answered, {correct} matching fictional author labels. Export a local JSON report with your answers and the stated limitations.</p></div><button onClick={exportResults} disabled={answered===0}>Download results (.json)</button></div>
      <div className="demo-feedback"><h3>What this demonstrates</h3><p>Negation and quantity mismatches are especially useful for showing why word overlap is not sufficient evidence grounding. Actual evaluator metrics are available separately in the research workspace when the backend is running.</p></div>
    </section>}
    {step===3&&<section className="demo-panel">
      <p className="demo-eyebrow">04 / RESEARCH GOVERNANCE</p><h2>Evaluation is not approval.</h2><p>Explore a preloaded illustrative release history. These records are local presentation examples, not actual Git commits, signed manifests, or persisted audit entries.</p>
      <div className="demo-metrics"><div><strong>Blocked</strong><span>Quality gate</span></div><div><strong>0 / 2</strong><span>Illustrative reviews</span></div><div><strong>{decision}</strong><span>Demo decision</span></div></div>
      <div className="demo-timeline">
        <div><span className="demo-dot"/><div><h3>Evaluation generated</h3><p>Fictional benchmark report created. No patient records or external model calls.</p></div></div>
        <div><span className="demo-dot"/><div><h3>Quality gates evaluated</h3><p>Human-review coverage missing. Release remains blocked by design.</p></div></div>
        {history&&<div><span className="demo-dot"/><div><h3>Illustrative audit event</h3><p>research_demo_001 · review_decision_recorded · {decision}</p></div></div>}
      </div>
      <fieldset className="demo-choices"><legend>Try a research review decision</legend><label className={decision==="pending"?"picked":""}><input type="radio" checked={decision==="pending"} onChange={()=>setDecision("pending")}/>Pending</label><label className={decision==="rejected"?"picked":""}><input type="radio" checked={decision==="rejected"} onChange={()=>setDecision("rejected")}/>Rejected</label></fieldset>
      <button onClick={()=>setHistory(true)}>{history?"Illustrative event recorded":"Simulate audit event"}</button>
      <p className="demo-muted">Approval is deliberately unavailable while review quality gates are blocked. This simulation does not write to the backend or audit log.</p>
    </section>}
    <footer className="demo-footer"><button className="demo-secondary" onClick={reset}>↺ Restart demo</button><div><button className="demo-secondary" disabled={step===0} onClick={()=>setStep(s=>s-1)}>← Back</button> <button onClick={()=>step===3?reset():setStep(s=>s+1)}>{step===3?"Start again":"Continue →"}</button></div></footer>
    <p className="demo-disclaimer">Synthetic educational demonstration only. No clinical validation, diagnosis, prescribing, or medical decisions. Illustrative model outputs and history are not live measurements.</p>
  </main>;
}
