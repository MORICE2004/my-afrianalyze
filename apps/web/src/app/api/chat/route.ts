import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { message, context_ticker } = await req.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    const apiUrl = process.env.API_URL_INTERNAL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${apiUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          context_ticker: context_ticker || 'NMB'
        }),
        signal: AbortSignal.timeout(8000)
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json({
          reply: data.reply,
          context_used: data.context_used
        });
      }
    } catch (fetchErr) {
      console.warn('Backend API unavailable for chat, falling back to safe offline explanation:', fetchErr);
    }

    // Graceful degraded response when backend API is offline
    return NextResponse.json({
      reply: `[AfriEdge Offline Notice] The AI Research Copilot requires connection to the backend Python engine for grounded evidence verification. Could not reach ${apiUrl}. Please verify the FastAPI service is running.`,
      status: 'OFFLINE_DEGRADED'
    });
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      { error: 'An error occurred while processing your request' },
      { status: 500 }
    );
  }
}
