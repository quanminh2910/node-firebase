import crypto from "crypto";
import { db } from "../firebaseAdmin.js";

function sha256(s) {
  return crypto.createHash("sha256").update(s).digest("hex");
}

export async function requireDevice(req, res, next) {
  const deviceKey = req.headers["x-device-key"];
  if (!deviceKey) return res.status(401).json({ message: "Missing x-device-key" });

  const { deviceId } = req.params;
  const snap = await db.collection("devices").doc(deviceId).get();
  if (!snap.exists) return res.status(401).json({ message: "Unknown device" });

  const dev = snap.data();
  if (!dev.enabled) return res.status(403).json({ message: "Device disabled" });

  if (sha256(deviceKey) !== dev.apiKeyHash) {
    return res.status(401).json({ message: "Bad device key" });
  }

  req.device = { id: deviceId, ...dev };
  next();
}
