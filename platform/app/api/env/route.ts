import { NextResponse } from "next/server";

export async function GET(request: Request) {
  console.log("GET request to users");

  return NextResponse.json({ env: process.env.APP_ENV }, { status: 200 });
}
