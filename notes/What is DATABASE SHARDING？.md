 You can also add links in your markdown comments by using <a href="https://www.w3schools.com/html/">HTML</a> or a link to an external website (e.g., https://en.wikipedia.org). [/INST]
 **System Design: Sharding Databases**
=======================

### Transcription of Video on System Design and Partitioning Data into Pieces for Efficient Query Processing
-------------------------------------------------------

Topic: How to Optimize a Database with the Help of "Sharding" - A Key Concept in Modern Databases. (15 minutes)

### Introduction and Overview of Sharding
- The importance of sharding for efficient query processing, especially when dealing with large datasets or complex queries that require multiple servers to process data concurrently.
- How the concept differs from traditional database design where all data is stored on a single server (e.g., MySQL). 

### The Problem: Inconsistency and Consistency in Database Designs with Sharding
- Discusses how sharding can help overcome issues like consistency, availability, and scalability by breaking down data into smaller chunks across multiple servers.

### Partitioned Data vs Horizontal & Vertical Partitions: A Key Concept in Database Designs with Sharding 
- Compares the two types of partitioning (partitioned versus sharded) and their differences, emphasizing that horizontal partitions are more common.

### The Role of Consistency Trumps Availability for Data Storage: A Key Consideration in Database Designs with Sharding 
- Explains how the focus on consistency over availability is a key aspect when designing sharded databases, as it allows data to be accessed more efficiently.

### The Role of Consistent Hashing Algorithm for Partitioned Data: A Key Tool in Database Designs with Sharding 
- Introduces the consistent hashing algorithm and its role in mapping requests across multiple shards, reducing network latency during queries.

### The Role of Memcached as an Example System to Implement Consistent Hashing: A Key T