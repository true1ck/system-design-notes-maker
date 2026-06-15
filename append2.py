import os

content = r'''

---

## Video 23: Data Consistency and Tradeoffs in Distributed Systems

### 1. Core Concepts Covered
*   **The Single Server Problem:** A single database server suffers from Single Point of Failure (SPOF), hard limits on Vertical Scaling, and high network latency for global users.
*   **The Consistency Challenge:** Once you replicate data across global servers to fix latency and SPOF, you introduce the problem of keeping the data copies perfectly in sync (Consistency).
*   **Two-Phase Commit (2PC):** A strong consistency protocol for distributed transactions across multiple databases.
    *   *Phase 1 (Prepare):* Leader asks followers to lock rows and prepare to commit.
    *   *Phase 2 (Commit/Rollback):* If all acknowledge, leader sends Commit. If anyone fails or times out, leader sends Rollback.
*   **Availability vs. Consistency:** 2PC locks resources. While waiting for network acknowledgments, reads and writes on those rows are blocked. The system becomes perfectly consistent but highly unavailable.
*   **Eventual Consistency:** In most modern web applications, blocking users is unacceptable. We accept that replicas might temporarily show stale data, as long as they *eventually* synchronize.

### 2. SDE 2/3 Depth & Missing Topics (2026 Focus)

> [!TIP]
> **CAP Theorem vs. PACELC Theorem**
> As a senior engineer, the CAP theorem is often too simplistic. You should discuss **PACELC**: *If there is a Partition (P), how does the system trade off Availability and Consistency (A and C); Else (E), when the system is running normally, how does it trade off Latency and Consistency (L and C)?*

*   **Read-Your-Own-Writes Consistency:** A specialized form of eventual consistency. If a user updates their profile picture, they should instantly see the new picture, even if the rest of the world sees the old one for a few minutes. Achieved by routing the user's subsequent reads to the Master node or caching locally.
*   **Quorum Reads/Writes:** In systems like Cassandra, you can tune consistency per request using $W + R > N$. (Write Quorum + Read Quorum > Total Replicas). This guarantees strong consistency without locking the entire database like 2PC.

### 3. Architecture Diagram: 2PC vs Eventual Consistency

```mermaid
graph TD
    subgraph Strict Consistency - 2PC
        L1[Leader DB] -->|1. Prepare| F1[Follower DB]
        F1 -->|2. ACK| L1
        L1 -->|3. Commit| F1
        F1 -.-x|Locked during 1-3| User[User Read - BLOCKED]
    end
    
    subgraph Eventual Consistency
        L2[Leader DB] -->|Async Replication| F2[Follower DB]
        L2 -.->|Instant Response| Client
        F2 -->|Read Stale Data| User2[User Read - FAST]
    end
```

### 4. Interview Questions
*   **Q:** *Why is a Two-Phase Commit (2PC) considered a bad fit for microservices?*
    *   **Answer:** Microservices are supposed to be independently deployable and highly available. 2PC creates tight temporal coupling; if a downstream billing service is slow to acknowledge, the upstream checkout service locks up. We use the Saga pattern instead.
*   **Q:** *How do you implement "Read-Your-Own-Writes" in an eventually consistent system?*
    *   **Answer:** When the user makes a write, we return an updated version token. The client passes this token on subsequent reads. If the replica being read hasn't caught up to that version token yet, the request is routed to the leader node or the replica waits.

---

## Video 24: System Design Interview: TikTok Architecture

### 1. Core Concepts Covered
*   **Requirements & Scale:** Designing a short-video platform (TikTok/Reels). 10M DAU, 100K Creators. Highly read-heavy system. Latency for upload can be minutes, but latency for viewing must be milliseconds.
*   **Database Choices:**
    *   *User Data:* MySQL (Relational) for structured profiles and ACID compliance.
    *   *Video Metadata:* NoSQL (MongoDB/DynamoDB) for flexible schema (tags, variable attributes) and massive read scaling.
    *   *Video Files:* Object Storage (AWS S3) combined with a CDN (Akamai/Cloudfront) for global distribution.
*   **Asynchronous Video Processing (Ingestion Pipeline):**
    *   Uploading a large video blocks the client. Instead, the upload is pushed to a Queue.
    *   Workers pull the video, chunk it, and parallelize the processing.
    *   The video is encoded into multiple formats (MP4, WebM) and resolutions (1080p, 720p, 480p) simultaneously by different workers.
*   **CDN Caching:** Viewers don't stream from S3. The Video Serving Service returns metadata with CDN URLs. The client streams directly from the nearest Edge node.

### 2. SDE 2/3 Depth & Missing Topics (2026 Focus)

> [!IMPORTANT]
> **Adaptive Bitrate Streaming (ABR)**
> Senior candidates must mention ABR (like HLS or DASH). You don't just send an MP4 file. The video is broken into 2-second `.ts` (Transport Stream) segments. The client continuously monitors network bandwidth and dynamically requests the next 2-second segment in either 1080p or 480p depending on real-time network conditions.

*   **Upload Optimization (Multipart Upload):** For uploading, SDEs should mention parallel chunked uploads. If a user is uploading a 50MB file and fails at 49MB, they shouldn't restart. Use S3 Multipart Upload to upload chunks in parallel and retry only failed chunks.
*   **Pre-fetching for Infinite Scroll:** TikTok's magic is zero buffering. The client downloads the metadata for the next 10 videos and pre-fetches the first 1-2 seconds of each video into local mobile cache while you are watching the current video.

### 3. Architecture Diagram: Video Ingestion & Delivery

```mermaid
graph LR
    Creator -->|1. Upload| API[API Gateway]
    API -->|2. Put Event| Queue[Kafka/SQS]
    
    subgraph Async Processing
        Queue --> W1[Worker - 1080p]
        Queue --> W2[Worker - 720p]
        Queue --> W3[Worker - 480p]
        W1 --> S3[(AWS S3)]
        W2 --> S3
        W3 --> S3
    end
    
    S3 -->|3. Push to Edge| CDN[CDN Edge Nodes]
    CDN -->|4. Stream Segments| Viewer
```

### 4. Interview Questions
*   **Q:** *In your TikTok design, how do you handle a viral video that suddenly gets 10 million views in an hour?*
    *   **Answer:** The CDN naturally absorbs this, but the *metadata* database (MongoDB) might get crushed by reads for likes/comments. We would put a Redis cache in front of the metadata DB. For likes/view counts, we wouldn't write to DB instantly; we'd aggregate counts in memory (or Redis) and flush to the DB periodically to save write IOPS.
*   **Q:** *Why split the video into multiple resolutions instead of letting the mobile phone downscale it?*
    *   **Answer:** Sending a 1080p video to a phone on a 3G network wastes massive amounts of bandwidth (costing money) and causes buffering. Providing a native 480p file saves network transit time and drastically reduces CPU decoding strain on low-end devices, saving battery life.

---

## Video 25 & 26: 5 Tips for System Design Interviews & HLD vs LLD

### 1. Core Concepts Covered
*   **Do Not Go Into Detail Prematurely:** Don't start defining TCP vs UDP or writing DB schemas in the first 5 minutes. Outline the High-Level boxes first, wait for the interviewer's feedback, and then dive deep where asked.
*   **Don't Have a Set Architecture in Mind:** Don't force every problem into a Kafka Pub/Sub model or Microservices just because you read a blog. Listen to the requirements.
*   **Keep It Simple, Stupid (KISS):** Don't overengineer with complex heartbeat servers or specific analytics databases unless the interviewer explicitly requests those features.
*   **Justify Your Choices:** Don't just say "I'll use Cassandra." Say "I'll use Cassandra because it's a masterless architecture that provides high availability and fast writes, which perfectly matches our massive write-heavy telemetry requirement."
*   **Be Aware of Technologies:** Know the landscape. Don't invent terms. Use industry standards: API Gateway, Kafka, Redis, S3, Cassandra, Postgres.
*   **HLD vs LLD:** 
    *   *High Level Design (HLD):* Focuses on architecture, load balancers, database choices, replication, queues.
    *   *Low Level Design (LLD):* Focuses on code, object-oriented design, Class Diagrams, Design Patterns (Strategy, Factory, Observer), and APIs.

### 2. SDE 2/3 Depth (2026 Focus)

> [!NOTE]
> **The Interview is a Conversation, Not a Presentation**
> For SDE 3 / Staff roles, the interviewer is evaluating if they want to work with you. If you get defensive when they challenge your architecture, it's a red flag. Acknowledge trade-offs: "You're right, introducing Kafka here adds operational complexity, but here is why I think the decoupling benefit outweighs it..."

*   **Capacity Estimation (Back-of-the-envelope):** Senior engineers must ground their designs in math. Don't guess. Estimate QPS, Storage per day, and Network Bandwidth. Use this math to justify whether a component needs horizontal scaling or if a single Redis instance is enough.
*   **Failure Scenarios:** Always dedicate the last 5 minutes to what happens when things break. "What if Redis dies?", "What if the CDN goes down?", "How do we recover from a split-brain?" 

### 3. Interview Framework

```mermaid
graph TD
    A[1. Clarify Requirements] --> B[2. Capacity Estimation]
    B --> C[3. API Design]
    C --> D[4. Data Model]
    D --> E[5. High-Level Design]
    E --> F[6. Deep Dives & Trade-offs]
```

### 4. Final System Design Checklist
*   [ ] Did I ask clarifying questions about Read vs Write ratios?
*   [ ] Did I identify the bottlenecks based on math?
*   [ ] Did I justify my Database choices based on ACID vs BASE?
*   [ ] Did I handle Single Points of Failure (SPOFs)?
*   [ ] Did I communicate trade-offs clearly?

---
'''

file_path = '/Users/chandresh_kerkar/Documents/Notes/System Design /notes maker/SDE2_3_System_Design_Notes.md'
with open(file_path, 'a') as f:
    f.write(content)
