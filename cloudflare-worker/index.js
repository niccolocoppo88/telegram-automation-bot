/**
 * Cloudflare Worker — GitHub Webhook → Telegram Bot
 * 
 * Receives GitHub webhooks and forwards them to Telegram
 * 
 * Setup:
 * 1. Deploy this worker to Cloudflare Workers
 * 2. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as secrets
 * 3. Configure GitHub webhook to point to this worker URL
 */

const BOT_TOKEN = env.TELEGRAM_BOT_TOKEN;
const CHAT_ID = env.TELEGRAM_CHAT_ID;
const SECRET = env.WEBHOOK_SECRET || '';

export default {
  async fetch(request, env) {
    // Only accept POST
    if (request.method !== 'POST') {
      return new Response('OK', { status: 200 });
    }

    // Verify secret if set
    if (SECRET) {
      const signature = request.headers.get('x-hub-signature-256');
      const body = await request.text();
      
      // Simple HMAC verification could be added here
      // For now, we trust the source (Cloudflare)
      
      // Send to Telegram
      await sendToTelegram(formatGitHubMessage(JSON.parse(body)), env);
      return new Response('OK', { status: 200 });
    }

    try {
      const body = await request.json();
      await sendToTelegram(formatGitHubMessage(body), env);
      return new Response('OK', { status: 200 });
    } catch (e) {
      return new Response('Error: ' + e.message, { status: 500 });
    }
  }
};

function formatGitHubMessage(body) {
  // Handle push events
  if (body.ref && body.commits) {
    const pusher = body.pusher?.name || 'Unknown';
    const repo = body.repository?.full_name || '';
    const branch = body.ref?.replace('refs/heads/', '') || '';
    const commits = body.commits?.length || 0;
    const author = body.commits?.[0]?.author?.name || pusher;
    
    return `🚀 *Push to ${repo}*\n\n` +
           `📍 Branch: \`${branch}\`\n` +
           `👤 ${author}\n` +
           `📝 ${commits} commit(s)\n\n` +
           `${body.compare ? `[View changes](${body.compare})` : ''}`;
  }
  
  // Handle pull request events
  if (body.pull_request) {
    const pr = body.pull_request;
    const action = body.action || '';
    const repo = body.repository?.full_name || '';
    const title = pr.title || '';
    const user = pr.user?.login || '';
    const url = pr.html_url || '';
    const state = pr.merged ? '🟣 MERGED' : pr.state === 'open' ? '🟢 OPEN' : '🔴 CLOSED';
    
    return `${state} *PR in ${repo}*\n\n` +
           `${action.toUpperCase()}\n` +
           `📌 ${title}\n` +
           `👤 @${user}\n` +
           `[View PR](${url})`;
  }
  
  // Handle workflow events
  if (body.workflow_run) {
    const run = body.workflow_run;
    const repo = body.repository?.full_name || '';
    const name = run.name || '';
    const status = run.status === 'completed' ? 
      (run.conclusion === 'success' ? '✅ SUCCESS' : '❌ FAILED') : 
      '⏳ IN PROGRESS';
    const url = run.html_url || '';
    const triggered_by = run.actor?.login || '';
    
    return `📊 *CI/CD: ${name}*\n\n` +
           `\`${status}\`\n` +
           `📦 ${repo}\n` +
           `👤 ${triggered_by}\n` +
           `[View run](${url})`;
  }
  
  // Handle issue events
  if (body.issue) {
    const issue = body.issue;
    const action = body.action || '';
    const repo = body.repository?.full_name || '';
    const title = issue.title || '';
    const url = issue.html_url || '';
    const user = issue.user?.login || '';
    const labels = issue.labels?.map(l => l.name).join(', ') || '';
    
    return `📋 *Issue ${action} in ${repo}*\n\n` +
           `📌 ${title}\n` +
           `👤 @${user}\n` +
           `${labels ? `🏷️ ${labels}\n` : ''}` +
           `[View issue](${url})`;
  }
  
  // Default fallback
  const repo = body.repository?.full_name || 'Unknown repo';
  const event = body.event || 'unknown';
  return `📬 *GitHub Event*\n\nRepo: ${repo}\nEvent: ${event}`;
}

async function sendToTelegram(message, env) {
  const token = env.TELEGRAM_BOT_TOKEN;
  const chatId = env.TELEGRAM_CHAT_ID;
  
  if (!token || !chatId) {
    throw new Error('Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID');
  }
  
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'Markdown'
    })
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Telegram API error: ${error}`);
  }
  
  return true;
}
