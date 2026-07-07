import express from 'express';
import { propertySearchHandler } from './routes/propertySearchRoute';

const app = express();

app.get('/properties/search', propertySearchHandler);

export default app;

import { propertyHistoryHandler } from './routes/propertyHistoryRoute';

app.get('/properties/:id/history', propertyHistoryHandler);
