import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ env: process.env.APP_ENV }, { status: 200 });
}
