const state={grants:[],query:"",category:"",match:"",status:"Open"};
const $=id=>document.getElementById(id);
const escapeHtml=s=>String(s??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const fmtDate=s=>!s||s==="Ongoing"?s||"Not listed":new Intl.DateTimeFormat("en-CA",{year:"numeric",month:"short",day:"numeric",timeZone:"UTC"}).format(new Date(`${s}T00:00:00Z`));
const daysTo=s=>!s||s==="Ongoing"?9999:Math.ceil((new Date(`${s}T23:59:59`)-new Date())/86400000);
const money=n=>new Intl.NumberFormat("en-CA",{style:"currency",currency:"CAD",notation:"compact",maximumFractionDigits:1}).format(n);

async function init(){
  try{const r=await fetch("data/grants.json",{cache:"no-store"});const data=await r.json();state.grants=data.grants||[];$("lastChecked").textContent=fmtDate(data.last_checked);setupFilters();render();}
  catch(e){$("grantGrid").innerHTML='<div class="empty"><strong>Grant data could not be loaded.</strong><span>Run the research workflow or check data/grants.json.</span></div>';}
}
function setupFilters(){
  [...new Set(state.grants.map(g=>g.category).filter(Boolean))].sort().forEach(c=>$("categoryFilter").insertAdjacentHTML("beforeend",`<option>${escapeHtml(c)}</option>`));
  [["searchInput","input","query"],["categoryFilter","change","category"],["matchFilter","change","match"],["statusFilter","change","status"]].forEach(([id,event,key])=>$(id).addEventListener(event,e=>{state[key]=e.target.value;render()}));
}
function filtered(){return state.grants.filter(g=>{
  const hay=[g.program,g.organization,g.description,g.category,g.fit_reason].join(" ").toLowerCase();
  const band=g.match_score>=80?"high":g.match_score>=60?"medium":"low";
  return(!state.query||hay.includes(state.query.toLowerCase()))&&(!state.category||g.category===state.category)&&(!state.match||band===state.match)&&(!state.status||g.status===state.status);
}).sort((a,b)=>b.match_score-a.match_score||daysTo(a.deadline)-daysTo(b.deadline));}
function render(){
  const active=state.grants.filter(g=>g.status==="Open"),high=active.filter(g=>g.match_score>=80),closing=active.filter(g=>daysTo(g.deadline)>=0&&daysTo(g.deadline)<=30),total=active.reduce((s,g)=>s+(Number(g.funding_max)||0),0),items=filtered();
  $("activeCount").textContent=active.length;$("newCount").textContent=`${active.filter(g=>g.is_new).length} new`;$("highCount").textContent=high.length;$("closingCount").textContent=closing.length;$("fundingTotal").textContent=total?money(total):"Not listed";$("resultCount").textContent=`${items.length} ${items.length===1?"opportunity":"opportunities"}`;
  $("grantGrid").innerHTML=items.map(card).join("");$("emptyState").hidden=items.length>0;
}
function card(g){const safeUrl=/^https:\/\//.test(g.official_url||"")?g.official_url:"#";return `<article class="grant-card">
  <div class="card-top"><div class="badges">${g.is_new?'<span class="badge new">New</span>':""}<span class="badge ${escapeHtml(g.status.toLowerCase())}">${escapeHtml(g.status)}</span><span class="badge">${escapeHtml(g.category)}</span></div><div class="score" style="--score:${Number(g.match_score)||0}"><span>${Number(g.match_score)||0}<small>MATCH</small></span></div></div>
  <p class="org">${escapeHtml(g.organization)}</p><h2>${escapeHtml(g.program)}</h2><p class="description">${escapeHtml(g.description)}</p>
  <div class="details"><div><span>Funding</span><strong>${escapeHtml(g.funding_amount||"Not listed")}</strong></div><div><span>Deadline</span><strong>${escapeHtml(fmtDate(g.deadline)||"Not listed")}</strong></div><div><span>Region</span><strong>${escapeHtml(g.province||"Canada-wide")}</strong></div><div><span>Type</span><strong>${escapeHtml(g.funding_type||"Grant")}</strong></div></div>
  <p class="fit"><strong>Why it fits:</strong> ${escapeHtml(g.fit_reason)}</p>
  <a class="official-link" href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer"><span>View official program</span><small>${escapeHtml(g.source_domain||"Government source")} ↗</small></a></article>`}
init();
