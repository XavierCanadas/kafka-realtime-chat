# Realtime chat with kafka
*Created by Xavier Cañadas*

## 1. Introduction
This project is a simplified version of a realtime chat application built using a microservice architecture, where each component focuses on a specific task. The system offers several key features and architectural benefits:

- **Distributed System**: The application is designed as a collection of loosely coupled services that work together, improving fault tolerance and enabling independent development and deployment of components.

- **Horizontal Scalability**: Each microservice can be independently scaled out to handle increasing loads. This architecture allows the system to efficiently accommodate growing numbers of users and messages by adding more instances of specific components as needed.

- **Kafka Integration**: Apache Kafka serves as the central message broker, enabling high-throughput, fault-tolerant communication between services. This ensures reliable message delivery even under high load or when components fail.

- **Technology Stack**:

    - **Client**: A native iOS mobile application built with SwiftUI
    - **Backend Services**: Multiple microservices implemented with Python FastAPI
    - **Message Broker**: Confluent Kafka for real-time event streaming
    - **Data Storage**: SQL database for user information and authentication, NoSQL database for efficient message storage and retrieval
    - **Local Deployment**: The entire system can be deployed locally using Docker containers, making development and testing straightforward while maintaining isolation between services.

This architecture allows for a responsive, reliable chat experience that can scale from a small prototype to a production system capable of handling numerous concurrent users and conversations.

## 2. Data Structure

## 3. System architecture
![Diagram of the architecture](<resources/Realtime chat architecture design.png>)

### 3.1 Client
The client is a mobile app built with SwiftUI. Users first need to log in to access the system. Once authenticated, they can initiate private conversations with other users or join existing group chats.

The app establishes a persistent WebSocket connection with the websocker servers, enabling real-time bidirectional communication. This allows messages to be sent and received instantly without polling the server.

All messages are stored on the server side. When a user opens a conversation, the app automatically requests and loads the message history from the server, ensuring users have access to the complete chat history regardless of which device they're using.

The users can create a channel and also join one that already exists. Inside the channel, the users can send and receive new messages and see the history.


### 3.2 WebSocket Server

The WebSocket Server acts as the real-time communication backbone of the system, managing bidirectional connections with client applications. Each server instance maintains numerous concurrent WebSocket connections with clients, enabling instant message delivery.

**Key characteristics**:

- **Horizontal Scalability**: The server is designed to scale horizontally to handle thousands of simultaneous connections. Additional server instances can be dynamically added to accommodate growing user loads.

- **Stateless Architecture**: To ensure reliability and fault tolerance, these servers are stateless. If one instance fails, connections can be re-established through other instances with minimal disruption.

- **Connection Management**: When a client establishes a WebSocket connection, the server registers this connection in Redis, creating a mapping between user IDs and server instances. This allows the system to route messages to the correct server instance.

- **Message Delivery**: 
    - **Send messages**: When a user sends a message in a channel, the WebSocket server receives it and produces the message to the message Kafka topic for further processing.
    - **Received messages**: The server provides an endpoint that receives messages intended for active clients. When message servers send data to this endpoint, the server forwards these messages to the appropriate clients through their active websocket connections.


### 3.3 Load Balancer

The Load Balancer serves as the single entry point for all client connections to the backend system. It plays a critical role in ensuring the system's reliability, scalability, and performance.

The Load Balancer dynamically routes incoming WebSocket connection requests from clients across multiple WebSocket Server instances.

### 3.4 Message Server

The Message Server is responsible for processing messages sent by clients. It acts as a Kafka consumer, retrieving messages from the appropriate topics for further handling.

**Key characteristics**:

- **Horizontal Scalability**: The server can be scaled horizontally with multiple instances organized as a consumer group to handle increasing message loads.

- **Message Processing Flow**:
    1. When consuming a message, it first identifies which channel the message belongs to.
    2. It then determines which users are members of that channel
    3. It queries Redis to locate the WebSocket server instances where these users are currently connected
    4. Once it has the list of active users and their connection points, it forwards the message to the corresponding WebSocket servers.

- **Persistent Storage**: In parallel with message delivery, it asynchronously stores each message in the message database, ensuring chat history is preserved for future reference.

- **Fault Tolerance**: As part of a Kafka consumer group, if one server instance fails, others can take over its workload with minimal disruption.

### 3.5 Kafka

Apache Kafka serves as the messaging backbone of the system, enabling reliable, high-throughput message delivery between components.

**Key characteristics**:

- **Topic Organization**: All messages from all channels are sent to a single topic called "Messages". This topic is configured with multiple partitions to enable parallel processing.

- **Message Structure**:

    - **Key**: Each message uses the channel ID as its key, ensuring that messages for the same channel are routed to the same partition
    - **Value**: The message payload contains the actual message content along with additional metadata (user ID, timestamp, etc.)
- **Ordering Guarantee**: By using the channel ID as the partition key, we ensure that all messages for a specific channel are processed in the exact order they were sent, maintaining conversation coherence

- **Scalability**: The partitioned design allows multiple consumer instances to process messages in parallel while preserving order within each channel






## 4. Implementation


## References
- Romaniuk, M. (February 26, 2024). System design: Chat Application - Mariia romaniuk - medium. Medium. https://medium.com/@m.romaniiuk/system-design-chat-application-1d6fbf21b372

- GeeksforGeeks. (June 2024). How Discord Scaled to 15 Million Users on One Server? GeeksforGeeks. https://www.geeksforgeeks.org/how-discord-scaled-to-15-million-users-on-one-server/

- Vishnevskiy, S. (July 6, 2017). How Discord Scaled Elixir to 5,000,000 Concurrent Users. Discord Blog. https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users

- Stanislav Vishnevskiy. (January 13, 2017). How Discord Stores Billions of Messages. Discord Blog. https://discord.com/blog/how-discord-stores-billions-of-messages

- Thangudu, S. (2023, April 11). Real-time messaging. Engineering at Slack. https://slack.engineering/real-time-messaging/

- GeeksforGeeks. (March 18, 2024). Designing WhatsApp Messenger | System Design. GeeksforGeeks. https://www.geeksforgeeks.org/designing-whatsapp-messenger-system-design/?ref=ml_lbp

