import { Router } from "express";
import { requireDevice } from "../middleware/authDevice.js";
import { heartbeat, nextCommand, commandResult } from "../controllers/deviceController.js";

const r = Router();
r.post("/device/:deviceId/heartbeat", requireDevice, heartbeat);
r.get("/device/:deviceId/next-command", requireDevice, nextCommand);
r.post("/device/:deviceId/command-result", requireDevice, commandResult);
export default r;
