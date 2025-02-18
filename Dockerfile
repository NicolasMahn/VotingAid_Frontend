# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set build arguments for secrets
ARG CHROMADB_HOST
ARG CHROMADB_PORT
ARG OPENAI_KEY

# Set environment variables for secrets
ENV CHROMADB_HOST=${CHROMADB_HOST}
ENV CHROMADB_PORT=${CHROMADB_PORT}
ENV OPENAI_KEY=${OPENAI_KEY}

# Expose the port the app runs on
EXPOSE 80

# Run the application
CMD ["python", "main.py"]