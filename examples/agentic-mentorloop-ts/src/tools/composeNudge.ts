import * as fs from 'fs';
import * as path from 'path';

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

interface Programme {
  programme_id: string;
  name: string;
  cadence_days: number;
  success_markers: string[];
}

export class ComposeNudge {
  private dataPath: string;

  constructor(dataPath: string = path.join(__dirname, '../../../data')) {
    this.dataPath = dataPath;
  }

  compose(engagementData: string, tips: string, pairId?: string): string {
    // Parse engagement data
    const matches = engagementData.match(/last_checkin_days=(\d+)/);
    const lastCheckinDays = matches ? parseInt(matches[1]) : 14;
    
    // Load data
    const users = this.loadUsers();
    const pairings = this.loadPairings();
    const programmes = this.loadProgrammes();
    
    // Find a dormant pair
    const targetPair = pairId 
      ? pairings.find(p => p.pair_id === pairId)
      : pairings[Math.floor(Math.random() * pairings.length)];
    
    if (!targetPair) {
      return 'Error: No pairing found';
    }
    
    const mentee = users.find(u => u.user_id === targetPair.mentee_id);
    const mentor = users.find(u => u.user_id === targetPair.mentor_id);
    const programme = programmes.find(p => p.programme_id === targetPair.programme_id);
    
    if (!mentee || !mentor || !programme) {
      return 'Error: Missing data for nudge composition';
    }
    
    // Extract a tip suggestion
    const tipMatch = tips.match(/\) ([^|]+)/);
    const tipText = tipMatch ? tipMatch[1].trim() : 'Stay connected with your mentor';
    
    // Compose nudge based on programme cadence
    const isOverdue = lastCheckinDays > programme.cadence_days;
    
    const suggestedQuestions = [
      "What's one win from this week you'd like to share?",
      "What challenge could benefit from another perspective?",
      "How are you progressing on your current goals?",
      "What's one thing you'd like feedback on?"
    ];
    
    const question = suggestedQuestions[Math.floor(Math.random() * suggestedQuestions.length)];
    
    let body = '';
    if (isOverdue) {
      body = `Hi ${mentee.first_name}, noticed it has been ${lastCheckinDays} days since your last check-in. ${tipText} Here's a gentle prompt you can use with ${mentor.first_name}: "${question}"`;
    } else {
      body = `Hi ${mentee.first_name}, great to see you're staying connected! Here's a conversation starter for your next session with ${mentor.first_name}: "${question}"`;
    }
    
    return `To: ${mentee.first_name}
Subject: Checking in on your ${programme.name} progress
Body: ${body}`;
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

  private loadProgrammes(): Programme[] {
    const filePath = path.join(this.dataPath, 'programmes.json');
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content);
  }
}