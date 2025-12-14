# Executive Summary

The ArgusAI uses an **event-driven architecture** that processes camera feeds through motion detection, generates natural language descriptions via AI models, and delivers real-time notifications to a web dashboard. The system prioritizes simplicity and privacy by storing semantic descriptions rather than video footage, making it suitable for security, accessibility, and home automation use cases.

**Key Architectural Principles:**
1. **Description-First:** Store event descriptions, not video (privacy + storage efficiency)
2. **Event-Driven:** Asynchronous processing triggered by motion detection
3. **Multi-Provider AI:** Support multiple AI models with automatic fallback
4. **Real-Time Updates:** WebSocket notifications for live event feed
5. **Zero-Config Database:** SQLite for plug-and-play deployment
6. **Single Camera MVP:** Designed to scale to multi-camera in Phase 2

---
