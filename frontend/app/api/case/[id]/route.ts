export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

/**
 * Proxy GET /api/case/{id} → FastAPI backend.
 * Powers shareable /?case={uuid} URLs by streaming the backend's saved-case
 * JSON straight back to the browser.
 */
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
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
