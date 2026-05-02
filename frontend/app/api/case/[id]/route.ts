export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function backendBase(req: Request): string {
  // See app/api/run/route.ts — Vercel multi-service auto-injects a relative
  // NEXT_PUBLIC_BACKEND_URL that fetch() can't resolve.
  if (process.env.VERCEL) {
    const u = new URL(req.url);
    return `${u.protocol}//${u.host}/_/backend`;
  }
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
}

/**
 * Proxy GET /api/case/{id} → FastAPI backend.
 * Powers shareable /?case={uuid} URLs by streaming the backend's saved-case
 * JSON straight back to the browser.
 */
export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const backend = backendBase(req);
  const upstream = await fetch(`${backend}/api/case/${encodeURIComponent(id)}`, {
    headers: { Accept: 'application/json' },
  });
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache, no-transform',
    },
  });
}
