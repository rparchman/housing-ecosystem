import { Request, Response } from 'express';
import { getPropertyHistory } from '../db/propertyHistoryRepository';

export async function propertyHistoryHandler(req: Request, res: Response) {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({ error: 'Property ID is required' });
    }

    const history = await getPropertyHistory(id);
    res.json(history);
  } catch (err) {
    console.error('Property history error', err);
    res.status(500).json({ error: 'Internal server error' });
  }
}
