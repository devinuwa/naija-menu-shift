import { NextResponse } from "next/server";
import { DEFAULT_BRIEF, exploreLocal, type Brief } from "@/lib/engine";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const MAX_REQUEST_BYTES = 12_000;
const ALLOWED_FIELDS = new Set(Object.keys(DEFAULT_BRIEF));

function error(message: string, status = 400) {
  return NextResponse.json({ error: message }, {
    status, headers: { "Cache-Control": "no-store" },
  });
}

/** Research-only endpoint. Never executes instructions or sends requests to arbitrary hosts. */
export async function POST(request: Request) {
  if (!(request.headers.get("content-type") ?? "").toLowerCase().includes("application/json")) {
    return error("Content-Type must be application/json", 415);
  }
  const declared = Number(request.headers.get("content-length") ?? 0);
  if (declared > MAX_REQUEST_BYTES) return error("Request exceeds 12 KB limit", 413);
  let raw: string;
  try { raw = await request.text(); } catch { return error("Unable to read request body"); }
  if (new TextEncoder().encode(raw).length > MAX_REQUEST_BYTES)
    return error("Request exceeds 12 KB limit", 413);
  let body: unknown;
  try { body = JSON.parse(raw); } catch { return error("Request body must be valid JSON"); }
  if (body === null || Array.isArray(body) || typeof body !== "object") {
    return error("Brief must be a JSON object");
  }
  const supplied = body as Record<string, unknown>;
  if (Object.keys(supplied).some((key) => !ALLOWED_FIELDS.has(key))) {
    return error("Unknown request field");
  }
  const brief = { ...DEFAULT_BRIEF, ...supplied } as Brief;
  try {
    const result = exploreLocal(brief);
    return NextResponse.json(result, { headers: { "Cache-Control": "no-store" } });
  } catch (err) {
    return error(err instanceof Error ? err.message : "Invalid brief");
  }
}
