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

# Ensure entrypoint is executable
RUN chmod +x docker-entrypoint.sh

# Expose the port that Vite's development server runs on
EXPOSE 5179

# Use entrypoint to ensure node_modules are populated
ENTRYPOINT ["./docker-entrypoint.sh"]

# Command to start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
