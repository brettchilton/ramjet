# frontend/Dockerfile

# Use a Node.js LTS (Long Term Support) image as the base
FROM node:20-slim

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json (if you use it)
# to leverage Docker's build cache.
# This step only runs if package.json changes.
COPY package.json .
# COPY package-lock.json . # Uncomment if you use package-lock.json

# Install dependencies
RUN npm install

# Copy the rest of the application code
# This copies your source files, vite.config.ts, etc.
COPY . .

# Expose the port that Vite's development server runs on
EXPOSE 5173

# Command to start the development server
# --host 0.0.0.0 makes it accessible from outside the container
# This command will be overridden by docker-compose.yml for development,
# but it's good practice to include a default.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]