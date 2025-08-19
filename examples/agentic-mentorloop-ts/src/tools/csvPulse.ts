import * as fs from 'fs';
import * as path from 'path';

interface CheckIn {
  pair_id: string;
  timestamp: string;
  mentee_score: number;
  mentor_score: number;
  notes: string;
}

interface Message {
  pair_id: string;
  timestamp: string;
  author_role: string;
  channel: string;
  text: string;
}

interface User {
  user_id: string;
  role: string;
  email: string;
  timezone: string;
  first_name: string;
  joined_at: string;
}

interface Pairing {
  pair_id: string;
  mentor_id: string;
  mentee_id: string;
  programme_id: string;
  started_at: string;
}

interface EngagementOptions {
  mode?: 'summary' | 'list';
  limit?: number;
  prompt?: string;
}

interface SummaryResult {
  type: 'summary';
  sample: number;
  dormant: number;
  balance: string;
  last_checkin_days: number;
}

interface ListResult {
  type: 'list';
  dormant_count: number;
  mentees: Array<{
    mentee_id: string;
    first_name: string;
    pair_id: string;
    last_checkin_days: number;
  }>;
}

interface ErrorResult {
  type: 'error';
  message: string;
  hint: string;
}

type EngagementResult = SummaryResult | ListResult | ErrorResult;

export class EngagementPulse {
  private dataPath: string;

  constructor(dataPath: string = path.join(__dirname, '../../../data')) {
    this.dataPath = dataPath;
  }

  run(options?: EngagementOptions): EngagementResult {
    try {
      const mode = options?.mode || 'summary';
      const limit = options?.limit || 5;
      
      const checkins = this.loadCheckins();
      const messages = this.loadMessages();
      const users = this.loadUsers();
      const pairings = this.loadPairings();
      
      const now = new Date();
      const pairStats = new Map<string, { lastCheckin: Date, balance: string, daysSince: number }>();
      
      // Analyse checkins
      checkins.forEach(checkin => {
        const pairId = checkin.pair_id;
        const checkinDate = new Date(checkin.timestamp);
        
        if (!pairStats.has(pairId) || checkinDate > pairStats.get(pairId)!.lastCheckin) {
          const daysSince = Math.floor((now.getTime() - checkinDate.getTime()) / (1000 * 60 * 60 * 24));
          pairStats.set(pairId, { lastCheckin: checkinDate, balance: 'balanced', daysSince });
        }
      });
      
      // Analyse message balance for last 50 messages per pair
      const pairMessages = new Map<string, Message[]>();
      messages.forEach(msg => {
        if (!pairMessages.has(msg.pair_id)) {
          pairMessages.set(msg.pair_id, []);
        }
        pairMessages.get(msg.pair_id)!.push(msg);
      });
      
      pairMessages.forEach((msgs, pairId) => {
        const recentMessages = msgs.slice(-50);
        const mentorCount = recentMessages.filter(m => m.author_role === 'mentor').length;
        const menteeCount = recentMessages.filter(m => m.author_role === 'mentee').length;
        
        let balance = 'balanced';
        if (mentorCount > menteeCount * 1.5) {
          balance = 'mentor_heavy';
        } else if (menteeCount > mentorCount * 1.5) {
          balance = 'mentee_heavy';
        }
        
        if (pairStats.has(pairId)) {
          pairStats.get(pairId)!.balance = balance;
        }
      });
      
      // Find dormant pairs (> 14 days)
      const dormantPairs: Array<{pairId: string, daysSince: number}> = [];
      pairStats.forEach((stats, pairId) => {
        if (stats.daysSince > 14) {
          dormantPairs.push({ pairId, daysSince: stats.daysSince });
        }
      });
      
      if (mode === 'list') {
        // Sort dormant pairs by days since last checkin (descending)
        dormantPairs.sort((a, b) => b.daysSince - a.daysSince);
        
        // Map to mentee information
        const dormantMentees = dormantPairs.slice(0, limit).map(({ pairId, daysSince }) => {
          const pairing = pairings.find(p => p.pair_id === pairId);
          if (!pairing) {
            return {
              mentee_id: 'unknown',
              first_name: 'Unknown',
              pair_id: pairId,
              last_checkin_days: daysSince
            };
          }
          
          const mentee = users.find(u => u.user_id === pairing.mentee_id);
          return {
            mentee_id: pairing.mentee_id,
            first_name: mentee?.first_name || 'Unknown',
            pair_id: pairId,
            last_checkin_days: daysSince
          };
        });
        
        return {
          type: 'list',
          dormant_count: dormantPairs.length,
          mentees: dormantMentees
        };
      } else {
        // Summary mode
        let maxDays = 0;
        pairStats.forEach(stats => {
          if (stats.daysSince > maxDays) maxDays = stats.daysSince;
        });
        
        // Get overall balance
        const balances = Array.from(pairStats.values()).map(s => s.balance);
        const overallBalance = balances.filter(b => b === 'mentor_heavy').length > balances.length / 2 
          ? 'mentor_heavy' 
          : balances.filter(b => b === 'mentee_heavy').length > balances.length / 2
          ? 'mentee_heavy'
          : 'balanced';
        
        return {
          type: 'summary',
          sample: pairStats.size,
          dormant: dormantPairs.length,
          balance: overallBalance,
          last_checkin_days: maxDays
        };
      }
    } catch (error) {
      return {
        type: 'error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        hint: 'Check that data files exist and are properly formatted'
      };
    }
  }

  private loadCheckins(): CheckIn[] {
    const filePath = path.join(this.dataPath, 'checkins.csv');
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    
    return lines.slice(1).map(line => {
      const values = line.split(',');
      return {
        pair_id: values[0],
        timestamp: values[1],
        mentee_score: parseInt(values[2]),
        mentor_score: parseInt(values[3]),
        notes: values[4]
      };
    });
  }

  private loadMessages(): Message[] {
    const filePath = path.join(this.dataPath, 'messages.csv');
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    
    return lines.slice(1).map(line => {
      const values = line.split(',');
      return {
        pair_id: values[0],
        timestamp: values[1],
        author_role: values[2],
        channel: values[3],
        text: values.slice(4).join(',')
      };
    });
  }

  private loadUsers(): User[] {
    const filePath = path.join(this.dataPath, 'users.csv');
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    
    return lines.slice(1).map(line => {
      const values = line.split(',');
      return {
        user_id: values[0],
        role: values[1],
        email: values[2],
        timezone: values[3],
        first_name: values[4],
        joined_at: values[5]
      };
    });
  }

  private loadPairings(): Pairing[] {
    const filePath = path.join(this.dataPath, 'pairings.csv');
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    
    return lines.slice(1).map(line => {
      const values = line.split(',');
      return {
        pair_id: values[0],
        mentor_id: values[1],
        mentee_id: values[2],
        programme_id: values[3],
        started_at: values[4]
      };
    });
  }
}