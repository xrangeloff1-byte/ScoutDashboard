// Scout Cloudflare monitor — read-only, separate from Beatrice.
// Uses public ScoutDashboard GitHub Actions evidence; never sends outreach.
const REPO = "xrangeloff1-byte/ScoutDashboard";
const WORKFLOWS = ["scout-autodrafts.yml", "scout-prospecting.yml", "scout-qualify.yml"];
async function github(path, token) {
  const headers = { "Accept": "application/vnd.github+json", "User-Agent": "Scout-Cloudflare-Monitor" };
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch("https://api.github.com/repos/" + REPO + path, {headers});
  if (!response.ok) throw new Error("GitHub HTTP " + response.status + " for " + path);
  return response.json();
}
async function report(env) {
  const results = await Promise.all(WORKFLOWS.map(async workflow => {
    try {
      const data = await github("/actions/workflows/" + workflow + "/runs?per_page=1", env.GITHUB_TOKEN);
      const run = data.workflow_runs?.[0];
      return {workflow, status: run?.status || "not_run", conclusion: run?.conclusion || null,
        updated_at: run?.updated_at || null, url: run?.html_url || null};
    } catch (error) {return {workflow, status: "error", error: String(error)};}
  }));
  return {service: "scout-automation", mode: "read_only", checked_at: new Date().toISOString(),
    workflows: results, errors: results.filter(x => x.status === "error").length};
}
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path === "/") return new Response("Scout monitor ready. GET /status for Scout workflow health.", {headers: {"content-type": "text/plain"}});
    if (path !== "/status") return new Response("Not found", {status:404});
    try {
      const data = await report(env);
      return Response.json(data, {status: data.errors ? 502 : 200, headers: {"cache-control": "no-store"}});
    } catch (error) {return Response.json({status:"error",error:String(error)}, {status:502});}
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(report(env).then(data => {
      console.log(JSON.stringify(data));
      if (data.errors) throw new Error("Scout monitor failed to fetch one or more workflows");
    }));
  }
};
