export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const upstream = await fetch(`${backend}/api/run`, {
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
