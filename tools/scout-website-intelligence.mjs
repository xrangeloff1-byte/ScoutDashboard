/**
 * Scout Website Intelligence v1 — passive, review-only website checks.
 * Usage: node tools/scout-website-intelligence.mjs https://example.com
 * Node 20+; no dependencies or paid APIs. Never performs intrusive testing.
 */
import { writeFile, mkdir } from 'node:fs/promises';
import { URL } from 'node:url';
import net from 'node:net';

const input = process.argv[2];
if (!input) { console.error('Usage: node tools/scout-website-intelligence.mjs https://example.com'); process.exit(2); }
function safeUrl(value) {
  const u = new URL(value);
  if (u.protocol !== 'https:' || u.username || u.password || u.port || !u.hostname.includes('.')) throw Error('Public HTTPS URL required');
  if (net.isIP(u.hostname) || /(^|\.)(localhost|local|internal|test|invalid)$/.test(u.hostname)) throw Error('Private or local targets prohibited');
  return u;
}
const root = safeUrl(input);
const origin = root.origin;
const limit = 8;
const timeout = 8000;
const queue = [root.href];
const visited = new Set();
const pages = [];
const findings = [];
const add = (type, severity, url, evidence, suggestion) => findings.push({type,severity,url,evidence,suggestion});
function extract(html, base, pattern) {
  const found = [];
  for (const m of html.matchAll(pattern)) {
    try { found.push(new URL(m[1], base)); } catch {}
  }
  return found;
}
async function fetchPublic(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {signal:controller.signal,redirect:'manual',headers:{'user-agent':'CairnflowScoutPassiveAudit/1.0 (review-only)'}});
    return response;
  } finally { clearTimeout(timer); }
}
try {
  while (queue.length && pages.length < limit) {
    const url = queue.shift();
    if (visited.has(url)) continue;
    visited.add(url);
    const u = safeUrl(url);
    if (u.origin !== origin) continue;
    let response;
    try { response = await fetchPublic(url); }
    catch(e) { add('fetch_error','medium',url,String(e.message),'Check site availability and networking'); continue; }
    const status = response.status;
    if (status >= 300 && status < 400) {
      add('redirect','info',url,'HTTP '+status,'Review redirect destination manually');
      continue;
    }
    if (!response.ok) { add('http_error','high',url,'HTTP '+status,'Repair inaccessible page'); continue; }
    const type = response.headers.get('content-type') || '';
    if (!type.includes('text/html')) continue;
    const html = (await response.text()).slice(0, 500000);
    const title = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.replace(/\s+/g,' ').trim() || '';
    const description = html.match(/<meta\s+[^>]*name=["']description["'][^>]*content=["']([^"']*)/i)?.[1] || '';
    const h1Count = (html.match(/<h1(?:\s|>)/gi)||[]).length;
    const images = (html.match(/<img(?:\s|>)[^>]*>/gi)||[]);
    const noAlt = images.filter(x=>!/\balt\s*=/.test(x)).length;
    pages.push({url,status,title,description,h1Count,images:images.length,imagesMissingAlt:noAlt});
    if (!title) add('seo_title','high',url,'Missing title','Write a descriptive, unique page title');
    if (!description) add('meta_description','medium',url,'Missing meta description','Add a useful search snippet');
    if (!h1Count) add('heading','medium',url,'No H1 found','Add a clear primary heading');
    if (h1Count > 1) add('heading','low',url,h1Count+' H1 elements','Review heading hierarchy');
    if (noAlt) add('accessibility','medium',url,noAlt+' images missing alt attribute','Add meaningful alt text where appropriate');
    if (!response.headers.get('content-security-policy')) add('security_header','info',url,'CSP header not observed','Review a suitable Content Security Policy');
    if (!response.headers.get('strict-transport-security')) add('security_header','info',url,'HSTS header not observed','Review HTTPS transport policy');
    for (const link of extract(html,url,/<a\b[^>]*\bhref\s*=\s*["']([^"']+)["']/gi)) {
      if (link.origin === origin && /^https:$/.test(link.protocol) && !visited.has(link.href) && !queue.includes(link.href) && queue.length < 30) queue.push(link.href);
    }
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  const report = {tool:'Cairnflow Scout passive website intelligence v1',target:origin,createdAt:new Date().toISOString(),mode:'review-only',limitations:['Sample of at most 8 pages','HTML heuristic checks only; not a vulnerability assessment','No automated outreach','No active penetration testing'],pages,findings,summary:{pagesReviewed:pages.length,findings:findings.length,high:findings.filter(x=>x.severity==='high').length}};
  await mkdir('operations',{recursive:true});
  await writeFile('operations/scout_website_intelligence.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report.summary,null,2));
} catch (e) { console.error('Scout audit failed:',e.message); process.exitCode=1; }
