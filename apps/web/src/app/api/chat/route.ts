import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // In a real implementation, this would connect to the PortfolioChatAgent
    // For now, returning a mock response simulating the AI agent's reply
    
    // Example of calling the Python backend/agent
    // const agentResponse = await fetch('http://localhost:8000/api/chat', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ message }),
    // });
    // const data = await agentResponse.json();
    
    const reply = `I received your question about the portfolio: "${message}". The PortfolioChatAgent is analyzing the African equity data and will provide a detailed response soon.`;

    return NextResponse.json({ reply });
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      { error: 'An error occurred while processing your request' },
      { status: 500 }
    );
  }
}
