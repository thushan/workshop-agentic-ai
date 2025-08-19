import * as fs from 'fs';
import * as path from 'path';
import { TipsRAG } from '../rag/tips';

interface Tip {
  tip_id: string;
  situation: string;
  text: string;
}

interface TipsResult {
  type: 'tips';
  hits: Array<{
    id: string;
    score: number;
    text: string;
    tags: string[];
  }>;
}

interface ErrorResult {
  type: 'error';
  message: string;
  hint: string;
}

export class MentorTips {
  private dataPath: string;
  private rag: TipsRAG;

  constructor(dataPath: string = path.join(__dirname, '../../../data')) {
    this.dataPath = dataPath;
    this.rag = new TipsRAG();
  }

  retrieve(query: string): TipsResult | ErrorResult {
    try {
      const tips = this.loadTips();
      const documents = tips.map(tip => ({
        id: tip.tip_id,
        text: `${tip.situation} ${tip.text}`,
        tags: tip.situation.split(/[,_\s]+/).filter(t => t.length > 0)
      }));
      
      const results = this.rag.findSimilar(query, documents, 2);
      
      if (results.length === 0) {
        return {
          type: 'tips',
          hits: []
        };
      }
      
      // Map results to structured format
      const hits = results.map(r => {
        const tip = tips.find(t => t.tip_id === r.id)!;
        return {
          id: r.id,
          score: parseFloat(r.score.toFixed(2)),
          text: tip.text,
          tags: r.tags || []
        };
      });
      
      return {
        type: 'tips',
        hits
      };
    } catch (error) {
      return {
        type: 'error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        hint: 'Check that tips.json exists and is properly formatted'
      };
    }
  }

  private loadTips(): Tip[] {
    const filePath = path.join(this.dataPath, 'tips.json');
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content);
  }
}