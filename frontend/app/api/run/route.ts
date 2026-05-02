export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

/**
 * On Vercel, route via the user's own host (e.g. resolvr-rosy.vercel.app)
 * instead of VERCEL_URL — VERCEL_URL points at the deployment-hash URL,
 * which is gated by Vercel's Deployment Protection (SSO 401). The user's
 * own alias is unguarded and routes through the same edge layer to the
 * backend service via the experimentalServices `routePrefix`.
 */
function backendBase(req: Request): string {
  if (process.env.NEXT_PUBLIC_BACKEND_URL) return process.env.NEXT_PUBLIC_BACKEND_URL;
  if (process.env.VERCEL) {
    const u = new URL(req.url);
    return `${u.protocol}//${u.host}/_/backend`;
  }
  return 'http://localhost:8000';
}

export async function GET(req: Request) {
  const backend = backendBase(req);
  const incoming = new URL(req.url);
  const qs = incoming.searchParams.toString();
  const url = qs ? `${backend}/api/run?${qs}` : `${backend}/api/run`;

  const upstream = await fetch(url, {
    headers: { Accept: 'text/event-stream' },
  });

  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
