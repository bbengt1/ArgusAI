# Performance Considerations

## Backend Optimizations

**Database:**
- Indexes on frequently queried columns (`events.timestamp`, `events.camera_id`)
- Connection pooling (SQLAlchemy default pool)
- Lazy loading for relationships
- Pagination for large result sets (max 200 per page)

**Image Processing:**
- Thumbnail generation asynchronous (BackgroundTasks)
- Compress thumbnails to <200KB JPEG
- Resize to 640x480 before storing
- Original frames discarded immediately after AI analysis

**Motion Detection:**
- Run in separate thread per camera
- Process at configurable FPS (default 5 FPS)
- Skip frames if processing can't keep up
- Background subtractor history: 500 frames

**AI API Calls:**
- Timeout: 10 seconds
- Retry with fallback provider on failure
- Queue if rate limit hit
- Cache provider availability status (5 min)

## Frontend Optimizations

**Next.js Features:**
- Server Components for initial page load (events, cameras)
- Client Components only where needed (forms, real-time)
- Image optimization via Next.js Image component
- Route prefetching for faster navigation

**Data Fetching:**
- SWR or React Query for caching API responses
- Optimistic updates for better UX
- Debounce search inputs (500ms)
- Virtual scrolling for large event lists

**WebSocket:**
- Single connection shared across app
- Automatic reconnection with exponential backoff
- Buffer messages during disconnect
- Heartbeat to detect stale connections

---
