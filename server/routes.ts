import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertCourseSchema, insertRoundSchema, insertShotSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Course routes
  app.get("/api/courses", async (req, res) => {
    try {
      const courses = await storage.getCourses();
      res.json(courses);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch courses" });
    }
  });

  app.get("/api/courses/nearby", async (req, res) => {
    try {
      const { lat, lng, radius } = req.query;
      if (!lat || !lng) {
        return res.status(400).json({ message: "Latitude and longitude are required" });
      }
      
      const courses = await storage.getCoursesByLocation(
        parseFloat(lat as string), 
        parseFloat(lng as string),
        radius ? parseFloat(radius as string) : undefined
      );
      res.json(courses);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch nearby courses" });
    }
  });

  app.get("/api/courses/:id", async (req, res) => {
    try {
      const course = await storage.getCourse(parseInt(req.params.id));
      if (!course) {
        return res.status(404).json({ message: "Course not found" });
      }
      res.json(course);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch course" });
    }
  });

  // Round routes
  app.get("/api/rounds", async (req, res) => {
    try {
      const { userId } = req.query;
      if (!userId) {
        return res.status(400).json({ message: "User ID is required" });
      }
      
      const rounds = await storage.getRounds(parseInt(userId as string));
      res.json(rounds);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch rounds" });
    }
  });

  app.get("/api/rounds/current", async (req, res) => {
    try {
      const { userId } = req.query;
      if (!userId) {
        return res.status(400).json({ message: "User ID is required" });
      }
      
      const round = await storage.getCurrentRound(parseInt(userId as string));
      res.json(round || null);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch current round" });
    }
  });

  app.post("/api/rounds", async (req, res) => {
    try {
      const validatedData = insertRoundSchema.parse(req.body);
      const round = await storage.createRound(validatedData);
      res.status(201).json(round);
    } catch (error) {
      res.status(400).json({ message: "Invalid round data", error });
    }
  });

  app.patch("/api/rounds/:id", async (req, res) => {
    try {
      const round = await storage.updateRound(parseInt(req.params.id), req.body);
      if (!round) {
        return res.status(404).json({ message: "Round not found" });
      }
      res.json(round);
    } catch (error) {
      res.status(500).json({ message: "Failed to update round" });
    }
  });

  // Shot routes
  app.get("/api/shots", async (req, res) => {
    try {
      const { roundId } = req.query;
      if (!roundId) {
        return res.status(400).json({ message: "Round ID is required" });
      }
      
      const shots = await storage.getShots(parseInt(roundId as string));
      res.json(shots);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch shots" });
    }
  });

  app.post("/api/shots", async (req, res) => {
    try {
      const validatedData = insertShotSchema.parse(req.body);
      const shot = await storage.createShot(validatedData);
      res.status(201).json(shot);
    } catch (error) {
      res.status(400).json({ message: "Invalid shot data", error });
    }
  });

  app.patch("/api/shots/:id", async (req, res) => {
    try {
      const shot = await storage.updateShot(parseInt(req.params.id), req.body);
      if (!shot) {
        return res.status(404).json({ message: "Shot not found" });
      }
      res.json(shot);
    } catch (error) {
      res.status(500).json({ message: "Failed to update shot" });
    }
  });

  // Weather proxy route
  app.get("/api/weather", async (req, res) => {
    try {
      const { lat, lon } = req.query;
      if (!lat || !lon) {
        return res.status(400).json({ message: "Latitude and longitude are required" });
      }

      const apiKey = process.env.OPENWEATHERMAP_API_KEY || process.env.WEATHER_API_KEY || "YOUR_OPENWEATHERMAP_API_KEY";
      
      const response = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=imperial`
      );

      if (!response.ok) {
        throw new Error(`Weather API responded with status: ${response.status}`);
      }

      const data = await response.json();
      res.json(data);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch weather data", error: error.message });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
