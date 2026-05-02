export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function backendBase(): string {
  if (process.env.NEXT_PUBLIC_BACKEND_URL) return process.env.NEXT_PUBLIC_BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}/_/backend`;
  return 'http://localhost:8000';
}

export async function GET(req: Request) {
  const backend = backendBase();
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
