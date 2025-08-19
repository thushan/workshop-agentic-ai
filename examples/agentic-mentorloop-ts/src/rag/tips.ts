export class TipsRAG {
  private stopWords = new Set([
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'the', 'this', 'your', 'you', 'our'
  ]);

  // Enhanced vectorisation with stop words and bigrams
  private vectorise(text: string): Map<string, number> {
    // Lowercase and strip punctuation
    const cleanText = text.toLowerCase().replace(/[^\w\s]/g, ' ');
    const words = cleanText.split(/\s+/).filter(w => w.length > 0);
    const vector = new Map<string, number>();
    
    // Add unigrams (single words)
    words.forEach(word => {
      if (word.length > 2 && !this.stopWords.has(word)) {
        vector.set(word, (vector.get(word) || 0) + 1);
      }
    });
    
    // Add bigrams (two-word phrases)
    for (let i = 0; i < words.length - 1; i++) {
      if (!this.stopWords.has(words[i]) && !this.stopWords.has(words[i + 1])) {
        const bigram = `${words[i]}_${words[i + 1]}`;
        vector.set(bigram, (vector.get(bigram) || 0) + 1);
      }
    }
    
    return vector;
  }
  
  // Cosine similarity between two vectors
  cosineSimilarity(vec1: Map<string, number>, vec2: Map<string, number>): number {
    const allWords = new Set([...vec1.keys(), ...vec2.keys()]);
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;
    
    allWords.forEach(word => {
      const v1 = vec1.get(word) || 0;
      const v2 = vec2.get(word) || 0;
      dotProduct += v1 * v2;
      norm1 += v1 * v1;
      norm2 += v2 * v2;
    });
    
    if (norm1 === 0 || norm2 === 0) return 0;
    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }
  
  findSimilar(query: string, documents: Array<{id: string, text: string, tags?: string[]}>, topK: number = 2): Array<{id: string, score: number, text: string, tags?: string[]}> {
    const queryVector = this.vectorise(query);
    
    const scores = documents.map(doc => {
      const docVector = this.vectorise(doc.text);
      const score = this.cosineSimilarity(queryVector, docVector);
      return { id: doc.id, score, text: doc.text, tags: doc.tags };
    });
    
    scores.sort((a, b) => b.score - a.score);
    return scores.slice(0, topK);
  }
}