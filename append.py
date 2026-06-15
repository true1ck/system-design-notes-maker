import os

content = r'''

---

## Video 20: How databases scale writes: The power of the log ✍️🗒️

### 1. Core Concepts Covered
*   **The Write Bottleneck:** Traditional SQL databases use B+ Trees. While B+ Trees provide excellent $O(\log N)$ read and write time theoretically, writing requires disk seeks, updating internal nodes, and rebalancing the tree. This random I/O makes high-volume writes a major bottleneck.
*   **The Speed of the Log:** If you want the fastest possible write speed, use an append-only log (like a Linked List). The time complexity is $O(1)$ because it's purely sequential I/O (just appending to the end of a file).
*   **The Read Problem:** A pure log is terrible for reading ($O(N)$ sequential scan).
*   **Log-Structured Merge-Trees (LSM-Trees):** A hybrid data structure used by modern NoSQL databases (Cassandra, RocksDB) to get $O(1)$ writes and fast reads. Data is written to an in-memory sorted structure, then flushed to disk as immutable **Sorted String Tables (SSTables)**.
*   **Compaction:** Because flushing creates many small SSTables, reading would require checking all of them. A background process called Compaction continuously merges smaller SSTables into larger ones (using a merge-sort algorithm), purging deleted/overwritten data.
*   **Bloom Filters:** To avoid scanning an SSTable on disk only to find the key isn't there, databases keep an in-memory Bloom Filter. It tells the DB "the key is *definitely not* here" or "the key *might* be here", drastically reducing useless disk reads.

### 2. SDE 2/3 Depth & Missing Topics (2026 Focus)

> [!TIP]
> **MemTables and Write-Ahead Logs (WAL)**
> The video simplifies the in-memory part. An SDE 3 must clarify: To survive a crash before the in-memory array is flushed to an SSTable, every write is *first* appended to a durable **Write-Ahead Log (WAL)** on disk. The WAL is only read during crash recovery. The actual serving of data happens from the in-memory **MemTable**.

*   **Tombstones:** Because SSTables are immutable, you cannot "delete" a row. Instead, you write a new record with a special "Tombstone" marker. During compaction, when the system merges a valid record and a Tombstone, it drops both, physically freeing the space.
*   **Read Amplification vs. Write Amplification:** 
    *   *Read Amplification:* Having to read multiple SSTables to find a value.
    *   *Write Amplification:* The same data being rewritten multiple times during background compaction.
    *   Tuning an LSM database is a constant battle between optimizing for Read vs Write amplification.

### 3. Architecture Diagram: LSM-Tree Write Path

```mermaid
graph TD
    Client -->|Write Key-Value| API[Database Node]
    
    API -->|1. Append (O-1)| WAL[(Write-Ahead Log on Disk)]
    API -->|2. Insert| MemTable[In-Memory MemTable: Red-Black Tree]
    
    MemTable -.->|3. Flush when full| SSTable1[(SSTable Level 0)]
    
    SSTable1 -.->|4. Background Compaction| SSTable2[(SSTable Level 1)]
```

### 4. Interview Questions
*   **Q:** *A user complains that your Cassandra database read latency sporadically spikes. What might be causing this?*
    *   **Answer:** It's likely a poorly tuned Compaction strategy. If compaction falls behind, reads must scan too many SSTables. Conversely, if major compaction kicks in during peak traffic, it starves the CPU and disk I/O, causing read queries to queue up and timeout.
*   **Q:** *How does a Bloom Filter work, and why does it have false positives but no false negatives?*
    *   **Answer:** A key is hashed using multiple hash functions to flip bits in a bit array. To check a key, you check those same bits. If even one bit is 0, the key is definitively *not* there (no false negatives). However, if all bits are 1, the key *might* be there, because other keys could have coincidentally flipped those exact bits (false positive).

---

## Video 21: Distributed Consensus and Data Replication strategies on the server

### 1. Core Concepts Covered
*   **Master-Slave Architecture:** To avoid a Single Point of Failure (SPOF) and scale reads, we replicate databases. A Master takes writes; Slaves take reads and copy data from the Master.
*   **Sync vs. Async Replication:** 
    *   *Synchronous:* Master waits for Slave to acknowledge the copy before returning success. Safe, but slow.
    *   *Asynchronous:* Master returns success immediately and copies to Slave in the background. Fast, but risks data loss if Master dies.
*   **Master-Master & Split Brain:** If two nodes accept writes, network failures can cause them to become isolated. They both think they are the leader and accept conflicting writes. When the network heals, you have a Split Brain problem (conflicting state).
*   **Quorum & Consensus:** To prevent Split Brain, you need an odd number of nodes (e.g., 3). If a partition happens, the side with the majority (Quorum) continues accepting writes; the minority halts. This requires Distributed Consensus.
*   **Saga Pattern & MVCC:** 
    *   *MVCC (Multi-Version Concurrency Control):* Keeps old versions of data so reads aren't blocked by writes (used in Postgres).
    *   *Saga:* For long-running distributed transactions (like food ordering), don't lock databases. Break it into local transactions and use compensating actions (rollbacks) if a step fails.

### 2. SDE 2/3 Depth & Missing Topics (2026 Focus)

> [!WARNING]
> **Raft and Paxos**
> The video glosses over *how* consensus is achieved. As an SDE 2/3, you must know that systems like ZooKeeper, etcd, and Kafka use **Raft** or **Paxos** algorithms. They rely on Leader Election and an Append-Entries log to ensure the cluster agrees on the sequence of state changes.

*   **Vector Clocks (Conflict Resolution):** In masterless systems (like DynamoDB), if a split-brain occurs and two conflicting writes happen, the database doesn't crash. It uses Vector Clocks (e.g., `[NodeA:2, NodeB:1]`) to detect the conflict and pushes both versions to the client application to resolve programmatically (e.g., merging shopping carts).
*   **Two-Phase Commit (2PC):** A strong consistency protocol for distributed transactions across multiple databases. 
    *   *Phase 1 (Prepare):* Coordinator asks all DBs to lock rows and prepare to commit.
    *   *Phase 2 (Commit):* If all say yes, coordinator says "commit." If one says no, coordinator says "rollback." It's incredibly slow and a blocking protocol, hence Sagas are preferred.

### 3. Architecture Diagram: Split Brain & Quorum

```mermaid
graph TD
    subgraph Network Partition
        NodeA[Node A - Master]
        NodeB[Node B - Follower]
        NodeC[Node C - Follower]
        
        NodeA <-->|Heartbeat| NodeB
        NodeA -.-x|Network Cut| NodeC
        NodeB -.-x|Network Cut| NodeC
    end
    
    NodeA -->|I can see B. We are 2/3 Quorum!| Active[Stay Active]
    NodeC -->|I see no one. I am 1/3 Minority.| Halt[Step Down / Read Only]
```

### 4. Interview Questions
*   **Q:** *Why is a Two-Phase Commit (2PC) considered an anti-pattern in high-throughput microservices?*
    *   **Answer:** 2PC holds strict database locks across multiple independent services while waiting for network acknowledgments. If the coordinator crashes during Phase 2, the locks remain held indefinitely. It fundamentally violates the independence and availability required in microservices.
*   **Q:** *If you are designing a highly available shopping cart service, would you prefer synchronous or asynchronous replication?*
    *   **Answer:** Asynchronous. Availability is prioritized over strict consistency (AP in CAP theorem). If a node dies and a user loses an item they just added to their cart, it's a minor annoyance. If synchronous replication causes the "Add to Cart" button to take 5 seconds or fail, you lose revenue.

---

## Video 22: Designing a location database: QuadTrees and Hilbert Curves

### 1. Core Concepts Covered
*   **The Proximity Problem:** Given a massive map, finding "users within 5km" using pure Euclidean math requires scanning every user in the database (which is $O(N)$ and too slow).
*   **Geohashing (Grid Partitioning):** Dividing the map using binary coordinates (e.g., bitwise latitude/longitude). This reduces search space, but a user on the border of a grid cell might be very close to a user in the adjacent cell, even though their binary prefixes look entirely different.
*   **QuadTrees:** A 2D tree where each node represents a bounding box. If a box contains too many users, it recursively splits into 4 smaller quadrants. It allows fast spatial querying but suffers from tree-rebalancing complexities when users move constantly.
*   **Space-Filling Curves (Z-Curve & Hilbert Curve):** The genius solution is to convert the 2D map into a 1D line using fractal curves. 
    *   Because 1D lines are easy to index (using B-Trees), we can map 2D coordinates to a 1D integer.
    *   *The Hilbert Curve* is preferred over the Z-Curve because it better preserves **spatial locality**: points close to each other on the 2D map are highly likely to be close to each other on the 1D Hilbert line.

### 2. SDE 2/3 Depth & Missing Topics (2026 Focus)

> [!IMPORTANT]
> **Read-Heavy vs. Write-Heavy Spatial Systems**
> QuadTrees are excellent for relatively static data (like finding restaurants). However, for a ride-sharing app where thousands of cars update their location every second, modifying a QuadTree is an absolute nightmare due to constant locking and node splitting. 
> For highly dynamic systems, **Redis Geospatial Indexes** (which under the hood use Geohashes mapped to Sorted Sets) are the industry standard.

*   **Geohash Edge Cases:** The "edge problem" happens when two points are physically 1 meter apart but lie on opposite sides of the Prime Meridian or Equator; their geohashes will share zero prefix bits. Queries must always check the target grid *plus its 8 neighboring grids* to guarantee accuracy.
*   **S2 Geometry & H3 (Uber):** SDE 3s must mention modern alternatives. 
    *   *Google S2:* Maps the sphere to a cube, using Hilbert curves on the cube faces. Fast and highly precise.
    *   *Uber H3:* Uses an **Hexagonal Grid System**. Unlike squares, hexagons are equidistant to all neighbors, making radius approximations and smoothing algorithms mathematically perfect for ride routing.

### 3. Architecture Diagram: Geospatial Indexing

```mermaid
graph LR
    App[Uber App] -->|Lat/Long: 40.7, -74.0| API[Location Service]
    
    API -->|1. Convert| S2[H3/Geohash Library]
    S2 -->|2. Hex Index: 892a10...| Cache[(Redis GeoHash Sorted Set)]
    
    Cache -->|3. ZRANGEBYLEX| API
    API -->|4. Return Nearby Drivers| App
```

### 4. Interview Questions
*   **Q:** *If you are designing Uber, how do you store the real-time locations of drivers moving every 3 seconds?*
    *   **Answer:** Do not use a persistent disk-based database like Postgres/PostGIS for real-time location pinging; it will burn out the disks. Use an in-memory datastore like Redis. You update the driver's Geohash in a Redis Sorted Set. A background worker can asynchronously bulk-persist the location history to an OLAP database for analytical purposes.
*   **Q:** *Why did Uber switch from Geohashes (rectangles) to H3 (hexagons) for surge pricing algorithms?*
    *   **Answer:** Rectangles have two types of neighbors: edge neighbors and vertex neighbors, which have different distances from the center. Hexagons have only one type of neighbor, all exactly equidistant. This makes calculating smoothed surge pricing gradients across a city computationally trivial and uniform.

'''

file_path = '/Users/chandresh_kerkar/Documents/Notes/System Design /notes maker/SDE2_3_System_Design_Notes.md'
with open(file_path, 'a') as f:
    f.write(content)
