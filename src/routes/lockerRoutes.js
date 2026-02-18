import { Router } from "express";
import { requireUser } from "../middleware/authUser.js";
import { listLockers, createLocker, requestUnlock } from "../controllers/lockerController.js";

const r = Router();
r.get("/lockers", requireUser, listLockers);
r.post("/lockers", requireUser, createLocker);
r.post("/lockers/:id/unlock", requireUser, requestUnlock);
export default r;
