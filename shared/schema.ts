import { pgTable, text, serial, integer, boolean, timestamp, decimal, json } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  handicap: decimal("handicap", { precision: 3, scale: 1 }),
  createdAt: timestamp("created_at").defaultNow(),
});

export const courses = pgTable("courses", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  location: text("location").notNull(),
  par: integer("par").notNull(),
  rating: decimal("rating", { precision: 3, scale: 1 }),
  slope: integer("slope"),
  holes: integer("holes").notNull().default(18),
  greenFee: decimal("green_fee", { precision: 8, scale: 2 }),
  latitude: decimal("latitude", { precision: 10, scale: 8 }),
  longitude: decimal("longitude", { precision: 11, scale: 8 }),
  createdAt: timestamp("created_at").defaultNow(),
});

export const rounds = pgTable("rounds", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id),
  courseId: integer("course_id").references(() => courses.id),
  date: timestamp("date").defaultNow(),
  totalScore: integer("total_score"),
  completed: boolean("completed").default(false),
  weather: json("weather"), // Store weather data as JSON
  currentHole: integer("current_hole").default(1),
  createdAt: timestamp("created_at").defaultNow(),
});

export const shots = pgTable("shots", {
  id: serial("id").primaryKey(),
  roundId: integer("round_id").references(() => rounds.id),
  hole: integer("hole").notNull(),
  score: integer("score"),
  club: text("club"),
  result: text("result"), // fairway, rough, bunker, green
  distance: integer("distance"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertUserSchema = createInsertSchema(users).omit({
  id: true,
  createdAt: true,
});

export const insertCourseSchema = createInsertSchema(courses).omit({
  id: true,
  createdAt: true,
});

export const insertRoundSchema = createInsertSchema(rounds).omit({
  id: true,
  createdAt: true,
});

export const insertShotSchema = createInsertSchema(shots).omit({
  id: true,
  createdAt: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export type InsertCourse = z.infer<typeof insertCourseSchema>;
export type Course = typeof courses.$inferSelect;

export type InsertRound = z.infer<typeof insertRoundSchema>;
export type Round = typeof rounds.$inferSelect;

export type InsertShot = z.infer<typeof insertShotSchema>;
export type Shot = typeof shots.$inferSelect;
