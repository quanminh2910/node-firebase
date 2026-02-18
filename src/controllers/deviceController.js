import { db, FieldValue } from "../firebaseAdmin.js";

export async function heartbeat(req, res) {
  const { deviceId } = req.params;
  const { status, fwVersion } = req.body;

  await db.collection("devices").doc(deviceId).update({
    lastHeartbeatAt: FieldValue.serverTimestamp(),
    ...(fwVersion ? { fwVersion } : {}),
  });

  // Update locker status too (optional)
  if (req.device.lockerId && status) {
    await db.collection("lockers").doc(req.device.lockerId).update({
      status,
      lastSeenAt: FieldValue.serverTimestamp(),
    });
  }

  res.json({ ok: true });
}

export async function nextCommand(req, res) {
  const { deviceId } = req.params;

  const q = await db.collection("commands")
    .where("status", "==", "PENDING")
    .limit(1)
    .get();

  if (q.empty) return res.json({ command: null });

  const doc = q.docs[0];
  const cmd = { id: doc.id, ...doc.data() };

  // Only give commands for this device’s locker
  if (cmd.lockerId !== req.device.lockerId) return res.json({ command: null });

  await db.collection("commands").doc(doc.id).update({
    status: "SENT",
    sentAt: FieldValue.serverTimestamp(),
  });

  res.json({ command: cmd });
}

export async function commandResult(req, res) {
  const { deviceId } = req.params;
  const { commandId, success, method, confidence, message } = req.body;

  if (!commandId) return res.status(400).json({ message: "commandId required" });

  const cmdRef = db.collection("commands").doc(commandId);
  const cmdSnap = await cmdRef.get();
  if (!cmdSnap.exists) return res.status(404).json({ message: "Command not found" });

  const cmd = cmdSnap.data();
  if (cmd.lockerId !== req.device.lockerId) return res.status(403).json({ message: "Wrong locker" });

  await cmdRef.update({
    status: success ? "DONE" : "FAILED",
    doneAt: FieldValue.serverTimestamp(),
    result: { message: message || null, confidence: confidence ?? null, method: method || null },
  });

  // Log it
  await db.collection("accessLogs").add({
    lockerId: cmd.lockerId,
    deviceId,
    userId: cmd.requestedBy || null,
    method: method || "DEVICE",
    success: !!success,
    confidence: confidence ?? null,
    createdAt: FieldValue.serverTimestamp(),
  });

  res.json({ ok: true });
}
