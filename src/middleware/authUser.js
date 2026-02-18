
import { auth } from "../firebaseAdmin.js";

export async function requireUser(req, res, next) {
  const header = req.headers.authorization || "";
  const m = header.match(/^Bearer (.+)$/);
  if (!m) return res.status(401).json({ message: "Missing Bearer token" });

  try {
    req.user = await auth.verifyIdToken(m[1]);
    next();
  } catch {
    return res.status(401).json({ message: "Invalid token" });
  }
}
