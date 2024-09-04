import { NextResponse } from "next/server";

export async function GET(request: Request) {
  return NextResponse.json({ env: process.env.APP_ENV }, { status: 200 });
}
