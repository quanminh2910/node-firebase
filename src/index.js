/*
import express from 'express';
import cors from 'cors';
import productRoute from './routes/productRoute.js';
import config from './config.js';

const app = express();

app.use(cors());
app.use(express.json());
app.use('/api', productRoute);

app.listen(config.port, () =>
  console.log(`Server is live @ ${config.hostUrl}`),
);
*/

import express from "express";
import cors from "cors";
import dotenv from "dotenv";

import lockerRoutes from "./routes/lockerRoutes.js";
import deviceRoutes from "./routes/deviceRoutes.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

app.get("/health", (req, res) => res.json({ ok: true }));

app.use("/api", lockerRoutes);
app.use("/api", deviceRoutes);

const port = process.env.PORT || 5000;
const host = process.env.HOST || "0.0.0.0";
app.listen(port, host, () => console.log(`API listening on http://${host}:${port}`));

