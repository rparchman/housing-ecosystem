import { Request, Response } from 'express';
import { parsePropertySearchQuery } from '../utils/parsePropertySearchQuery';
import { searchProperties } from '../db/propertySearchRepository';

export async function propertySearchHandler(req: Request, res: Response) {
  try {
    const query = parsePropertySearchQuery(req.query);
    const { results, total } = await searchProperties(query);

    const page = query.page || 1;
    const limit = query.limit || 25;
    const totalPages = Math.max(Math.ceil(total / limit), 1);

    res.setHeader('X-Total-Count', total.toString());
    res.setHeader('X-Total-Pages', totalPages.toString());
    res.setHeader('X-Page', page.toString());
    res.setHeader('X-Limit', limit.toString());

    res.json(results);
  } catch (err) {
    console.error('Property search error', err);
    res.status(500).json({ error: 'Internal server error' });
  }
}
