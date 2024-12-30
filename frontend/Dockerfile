FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV SKIP_TYPE_CHECK=true
ENV NEXT_DISABLE_ESLINT=1

# Build the application
RUN SKIP_TYPE_CHECK=true NEXT_DISABLE_ESLINT=1 npm run build

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["npm", "start"] 