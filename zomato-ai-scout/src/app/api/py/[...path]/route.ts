import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";

import type { ApiMetadata } from "@/lib/api-metadata";

export const runtime = "nodejs";

function backendBase(): string | null {
  const raw = process.env.BACKEND_URL?.trim().replace(/\/$/, "");
  if (!raw) return null;
  if (raw.includes("127.0.0.1") || raw.includes("localhost")) return null;
  if (raw.includes("streamlit.app")) return null;
  return raw;
}

let metadataCache: ApiMetadata | null = null;

async function bundledMetadata(): Promise<ApiMetadata> {
  if (metadataCache) return metadataCache;
  const file = path.join(process.cwd(), "public", "api-metadata.json");
  const raw = await readFile(file, "utf-8");
  metadataCache = JSON.parse(raw) as ApiMetadata;
  return metadataCache;
}

async function staticMetadataResponse(
  segments: string[],
  searchParams: URLSearchParams,
): Promise<NextResponse | null> {
  if (segments.length === 1 && segments[0] === "locations") {
    const meta = await bundledMetadata();
    return NextResponse.json({ locations: meta.locations });
  }

  if (segments.length === 1 && segments[0] === "cuisines") {
    const loc = searchParams.get("location")?.trim() ?? "";
    const meta = await bundledMetadata();
    const cuisines = loc ? (meta.cuisines_by_location[loc] ?? []) : [];
    return NextResponse.json({ cuisines });
  }

  return null;
}

async function proxyToBackend(
  req: NextRequest,
  segments: string[],
): Promise<NextResponse> {
  const base = backendBase();
  if (!base) {
    const fallback = await staticMetadataResponse(segments, req.nextUrl.searchParams);
    if (fallback) return fallback;

    return NextResponse.json(
      {
        detail:
          "API not configured. Set BACKEND_URL on Vercel to your FastAPI URL (Render), not Streamlit. " +
          "See zomato-ai-scout/README.md.",
      },
      { status: 503 },
    );
  }

  const target = `${base}/${segments.join("/")}${req.nextUrl.search}`;
  const headers = new Headers();
  const accept = req.headers.get("accept");
  if (accept) headers.set("accept", accept);
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const idempotency = req.headers.get("idempotency-key");
  if (idempotency) headers.set("idempotency-key", idempotency);

  const init: RequestInit = {
    method: req.method,
    headers,
    cache: "no-store",
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch (e) {
    const fallback = await staticMetadataResponse(segments, req.nextUrl.searchParams);
    if (fallback) return fallback;

    return NextResponse.json(
      {
        detail:
          e instanceof Error
            ? `Backend unreachable: ${e.message}`
            : "Backend unreachable.",
      },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const fallback = await staticMetadataResponse(segments, req.nextUrl.searchParams);
    if (fallback && upstream.status >= 500) return fallback;
  }

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

type RouteCtx = { params: Promise<{ path: string[] }> };

async function handle(req: NextRequest, ctx: RouteCtx) {
  const { path: segments } = await ctx.params;
  return proxyToBackend(req, segments);
}

export async function GET(req: NextRequest, ctx: RouteCtx) {
  return handle(req, ctx);
}

export async function POST(req: NextRequest, ctx: RouteCtx) {
  return handle(req, ctx);
}
