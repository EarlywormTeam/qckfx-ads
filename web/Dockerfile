# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y nodejs npm

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app

# Build React app
WORKDIR /app/frontend
RUN npm ci && \
    npm run build

# Return to the main app directory
WORKDIR /app

# Make port 8000 available to the world outside this container
EXPOSE 8000

COPY startup.sh /usr/local/bin/

RUN chmod u+x /usr/local/bin/startup.sh

ENTRYPOINT ["startup.sh"]
