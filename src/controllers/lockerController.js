import { db, FieldValue } from "../firebaseAdmin.js";

export async function listLockers(req, res) {
  const qs = await db.collection("lockers").get();
  res.json(qs.docs.map(d => ({ id: d.id, ...d.data() })));
}

export async function createLocker(req, res) {
  const { name, deviceId } = req.body;
  if (!name || !deviceId) return res.status(400).json({ message: "name & deviceId required" });

  const ref = await db.collection("lockers").add({
    name,
    deviceId,
    status: "LOCKED",
    lastSeenAt: null,
  });

  res.status(201).json({ id: ref.id });
}

export async function requestUnlock(req, res) {
  const lockerId = req.params.id;

  const lockerSnap = await db.collection("lockers").doc(lockerId).get();
  if (!lockerSnap.exists) return res.status(404).json({ message: "Locker not found" });

  const cmdRef = await db.collection("commands").add({
    lockerId,
    type: "UNLOCK",
    requestedBy: req.user.uid,
    status: "PENDING",
    createdAt: FieldValue.serverTimestamp(),
    sentAt: null,
    doneAt: null,
    result: null,
  });

  res.status(202).json({ commandId: cmdRef.id });
}
