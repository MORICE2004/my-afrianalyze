import type { NextRequest } from "next/server";
import { signIn } from "../_signin";

export async function POST(req: NextRequest) {
  return signIn(req, "/api/v1/auth/login");
}
