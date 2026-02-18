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
