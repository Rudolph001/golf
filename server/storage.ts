import { users, courses, rounds, shots, type User, type InsertUser, type Course, type InsertCourse, type Round, type InsertRound, type Shot, type InsertShot } from "@shared/schema";

export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // Course methods
  getCourses(): Promise<Course[]>;
  getCourse(id: number): Promise<Course | undefined>;
  getCoursesByLocation(lat: number, lng: number, radiusKm?: number): Promise<Course[]>;
  createCourse(course: InsertCourse): Promise<Course>;

  // Round methods
  getRounds(userId: number): Promise<Round[]>;
  getRound(id: number): Promise<Round | undefined>;
  createRound(round: InsertRound): Promise<Round>;
  updateRound(id: number, updates: Partial<Round>): Promise<Round | undefined>;
  getCurrentRound(userId: number): Promise<Round | undefined>;

  // Shot methods
  getShots(roundId: number): Promise<Shot[]>;
  createShot(shot: InsertShot): Promise<Shot>;
  updateShot(id: number, updates: Partial<Shot>): Promise<Shot | undefined>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private courses: Map<number, Course>;
  private rounds: Map<number, Round>;
  private shots: Map<number, Shot>;
  private currentUserId: number;
  private currentCourseId: number;
  private currentRoundId: number;
  private currentShotId: number;

  constructor() {
    this.users = new Map();
    this.courses = new Map();
    this.rounds = new Map();
    this.shots = new Map();
    this.currentUserId = 1;
    this.currentCourseId = 1;
    this.currentRoundId = 1;
    this.currentShotId = 1;

    // Initialize with some sample courses
    this.initializeSampleData();
  }

  private initializeSampleData() {
    const sampleCourses: InsertCourse[] = [
      {
        name: "Pebble Beach Golf Links",
        location: "Pebble Beach, CA",
        par: 72,
        rating: "75.5",
        slope: 144,
        holes: 18,
        greenFee: "595.00",
        latitude: "36.5694",
        longitude: "-121.9595"
      },
      {
        name: "Spyglass Hill Golf Course",
        location: "Pebble Beach, CA",
        par: 72,
        rating: "76.8",
        slope: 148,
        holes: 18,
        greenFee: "425.00",
        latitude: "36.5831",
        longitude: "-121.9550"
      },
      {
        name: "Monterey Peninsula Country Club",
        location: "Pebble Beach, CA",
        par: 71,
        rating: "74.2",
        slope: 142,
        holes: 18,
        greenFee: "350.00",
        latitude: "36.5889",
        longitude: "-121.9444"
      }
    ];

    sampleCourses.forEach(course => {
      this.createCourse(course);
    });
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user: User = { 
      ...insertUser, 
      id,
      createdAt: new Date()
    };
    this.users.set(id, user);
    return user;
  }

  // Course methods
  async getCourses(): Promise<Course[]> {
    return Array.from(this.courses.values());
  }

  async getCourse(id: number): Promise<Course | undefined> {
    return this.courses.get(id);
  }

  async getCoursesByLocation(lat: number, lng: number, radiusKm: number = 50): Promise<Course[]> {
    const courses = Array.from(this.courses.values());
    
    // Simple distance calculation (not perfectly accurate but good enough for demo)
    return courses.filter(course => {
      if (!course.latitude || !course.longitude) return false;
      
      const courseLat = parseFloat(course.latitude);
      const courseLng = parseFloat(course.longitude);
      
      const distance = Math.sqrt(
        Math.pow(lat - courseLat, 2) + Math.pow(lng - courseLng, 2)
      ) * 111; // Rough conversion to km
      
      return distance <= radiusKm;
    });
  }

  async createCourse(insertCourse: InsertCourse): Promise<Course> {
    const id = this.currentCourseId++;
    const course: Course = { 
      ...insertCourse, 
      id,
      createdAt: new Date()
    };
    this.courses.set(id, course);
    return course;
  }

  // Round methods
  async getRounds(userId: number): Promise<Round[]> {
    return Array.from(this.rounds.values()).filter(round => round.userId === userId);
  }

  async getRound(id: number): Promise<Round | undefined> {
    return this.rounds.get(id);
  }

  async createRound(insertRound: InsertRound): Promise<Round> {
    const id = this.currentRoundId++;
    const round: Round = { 
      ...insertRound, 
      id,
      date: new Date(),
      createdAt: new Date()
    };
    this.rounds.set(id, round);
    return round;
  }

  async updateRound(id: number, updates: Partial<Round>): Promise<Round | undefined> {
    const round = this.rounds.get(id);
    if (!round) return undefined;
    
    const updatedRound = { ...round, ...updates };
    this.rounds.set(id, updatedRound);
    return updatedRound;
  }

  async getCurrentRound(userId: number): Promise<Round | undefined> {
    return Array.from(this.rounds.values()).find(
      round => round.userId === userId && !round.completed
    );
  }

  // Shot methods
  async getShots(roundId: number): Promise<Shot[]> {
    return Array.from(this.shots.values()).filter(shot => shot.roundId === roundId);
  }

  async createShot(insertShot: InsertShot): Promise<Shot> {
    const id = this.currentShotId++;
    const shot: Shot = { 
      ...insertShot, 
      id,
      createdAt: new Date()
    };
    this.shots.set(id, shot);
    return shot;
  }

  async updateShot(id: number, updates: Partial<Shot>): Promise<Shot | undefined> {
    const shot = this.shots.get(id);
    if (!shot) return undefined;
    
    const updatedShot = { ...shot, ...updates };
    this.shots.set(id, updatedShot);
    return updatedShot;
  }
}

export const storage = new MemStorage();
